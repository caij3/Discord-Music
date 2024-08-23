import discord
import os
import asyncio
import yt_dlp
import random
from dotenv import load_dotenv
from discord.ext import commands
import urllib.parse, urllib.request, re

def run_bot():
    load_dotenv()
    TOKEN = os.getenv('TOKEN')
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix='!', intents=intents)

    yt_base_url = "https://www.youtube.com/"
    yt_results_url = yt_base_url + "results?"
    yt_watch_url = yt_base_url + "watch?v="

    voice_clients = {}
    song_queue = {}
    current_songs = {}
    loop_status = {}  # Track loop status per guild
    cached_streams = {}  # Cache for currently playing song streams
    processing_flags = {}  # Track if a song is currently being processed

    #yt_dlp_options = {"format": "bestaudio/best"}
    yt_dlp_options = {
        'format': 'bestaudio/best',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'ignoreerrors': False,
        'default_search': 'auto',
        'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
    }
    ytdl = yt_dlp.YoutubeDL(yt_dlp_options)

    ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                      'options': '-vn -filter:a "volume=0.50"'}

    @bot.event
    async def on_ready():
        print(f'{bot.user} has connected to Discord!')
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands.")

    async def play_next(interaction: discord.Interaction):
        guild_id = interaction.guild.id

        # Set processing flag to True to prevent other operations
        processing_flags[guild_id] = True

        if loop_status.get(guild_id, False):  # If loop is enabled
            stream_url = cached_streams.get(guild_id)
            if stream_url:
                await play_song(interaction, stream_url, cached=True)
        else:
            if song_queue[guild_id]:
                url = song_queue[guild_id].pop(0)
                await play_song(interaction, url)
            else:
                await bot.change_presence(status=None)
                current_songs[guild_id] = None
                await interaction.followup.send("The queue is empty.")
        
        # Clear processing flag
        processing_flags[guild_id] = False

    async def play_song(interaction: discord.Interaction, url: str, cached=False):
        guild_id = interaction.guild.id
        voice_client = voice_clients[guild_id]

        try:
            if not cached:
                if yt_base_url not in url:
                    url = _search_url(url)
                
                if "playlist?" in url:
                    await interaction.followup.send("Cannot play playlists. Please provide a single video URL.")
                    print("Playlist: " + url)
                    return

                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))

                stream_url = data['url']
                title = data['title']
                cached_streams[guild_id] = stream_url

            else:
                stream_url = cached_streams[guild_id]
                title = current_songs[guild_id][0]

            player = discord.FFmpegOpusAudio(stream_url, **ffmpeg_options)

            def after_play(error):
                if error:
                    print(f"Error in after_play: {error}")
                # Check if another song is currently being processed
                if processing_flags.get(guild_id, False):
                    print("Another song is being processed, returning.")
                    return
                coro = play_next(interaction)
                fut = asyncio.run_coroutine_threadsafe(coro, bot.loop)
                try:
                    fut.result()
                except Exception as e:
                    print(f"Error handling after play: {e}")

            voice_client.play(player, after=after_play)
            current_songs[guild_id] = (title, url)  # Update the current song
            await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.custom, name="custom", state="Now playing: " + title))

            if not cached:
                await interaction.followup.send(f"Now playing: {title}")

        except Exception as e:
            print(f"An error occurred in play_song: {e}")
            await interaction.followup.send("Something went wrong while trying to play the song.")

    @bot.tree.command(name="play", description="Play a song from a URL")
    async def play(interaction: discord.Interaction, url: str):
        await interaction.response.defer()

        guild_id = interaction.guild.id
        if guild_id not in voice_clients:
            if interaction.user.voice:
                channel = interaction.user.voice.channel
                voice_client = await channel.connect()
                await voice_client.guild.change_voice_state(channel=channel, self_deaf=True)
                voice_clients[guild_id] = voice_client
                song_queue[guild_id] = []
                loop_status[guild_id] = False
                cached_streams[guild_id] = None
            else:
                await interaction.followup.send("You are not connected to a voice channel.")
                return

        voice_client = voice_clients[guild_id]

        if voice_client.is_playing():
            await interaction.followup.send("Already playing a song. Adding to the queue.")
            print(url)
            song_queue[guild_id].append(url)
        else:
            await play_song(interaction, url)

    @bot.tree.command(name="playing", description="Show the currently playing song")
    async def playing(interaction: discord.Interaction):
        guild_id = interaction.guild.id
        if guild_id in current_songs and current_songs[guild_id]:
            await interaction.response.send_message(f"Currently playing: {current_songs[guild_id][0]}\n{current_songs[guild_id][1]}")
        else:
            await interaction.response.send_message("No song is currently playing.")

    @bot.tree.command(name="pause", description="Pause the current song")
    async def pause(interaction: discord.Interaction):
        try:
            if interaction.guild.id in voice_clients:
                voice_client = voice_clients[interaction.guild.id]
                if voice_client.is_playing():
                    voice_client.pause()
                    await interaction.response.send_message("Song paused.")
                else:
                    await interaction.response.send_message("No song is currently playing.")
            else:
                await interaction.response.send_message("Not connected to a voice channel.")
        except Exception as e:
            print(f"An error occurred in pause: {e}")
            await interaction.response.send_message("Something went wrong while trying to pause the song.")

    @bot.tree.command(name="resume", description="Resume the paused song")
    async def resume(interaction: discord.Interaction):
        try:
            if interaction.guild.id in voice_clients:
                voice_client = voice_clients[interaction.guild.id]
                if voice_client.is_paused():
                    voice_client.resume()
                    await interaction.response.send_message("Song resumed.")
                else:
                    await interaction.response.send_message("No song is currently paused.")
            else:
                await interaction.response.send_message("Not connected to a voice channel.")
        except Exception as e:
            print(f"An error occurred in resume: {e}")
            await interaction.response.send_message("Something went wrong while trying to resume the song.")

    @bot.tree.command(name="stop", description="Stop the current song")
    async def stop(interaction: discord.Interaction):
        try:
            guild_id = interaction.guild.id
            if guild_id in voice_clients:
                voice_client = voice_clients[interaction.guild.id]
                voice_client.stop()
                song_queue[interaction.guild.id] = []  # Clear the queue
                cached_streams[guild_id] = None  # Clear the cache
                await interaction.response.send_message("Song stopped and queue cleared.")
            else:
                await interaction.response.send_message("Not connected to a voice channel.")
        except Exception as e:
            print(f"An error occurred in stop: {e}")
            await interaction.response.send_message("Something went wrong while trying to stop the song.")

    @bot.tree.command(name="leave", description="Make the bot leave")
    async def leave(interaction: discord.Interaction):
        try:
            guild_id = interaction.guild.id
            if guild_id in voice_clients:
                voice_client = voice_clients[interaction.guild.id]
                await voice_client.disconnect()
                del voice_clients[guild_id]
                del song_queue[guild_id]
                del loop_status[guild_id]  # Remove loop status
                cached_streams[guild_id] = None  # Clear the cache
                await interaction.response.send_message("Left the voice channel.")
            else:
                await interaction.response.send_message("Not connected to a voice channel.")
        except Exception as e:
            print(f"An error occurred in leave: {e}")
            await interaction.response.send_message("Something went wrong while trying to leave the voice channel.")

    @bot.tree.command(name="queue", description="View the current song queue")
    async def queue(interaction: discord.Interaction):
        guild_id = interaction.guild.id
        if guild_id in song_queue and song_queue[guild_id]:
            queue_list = song_queue[guild_id]
            queue_str = "\n".join([f"{i + 1}. {url}" for i, url in enumerate(queue_list)])
            await interaction.response.send_message(f"Current queue:\n{queue_str}")
        else:
            await interaction.response.send_message("The queue is currently empty.")

    @bot.tree.command(name="clear_queue", description="Clear the current song queue")
    async def clear_queue(interaction: discord.Interaction):
        guild_id = interaction.guild.id
        if guild_id in song_queue and song_queue[guild_id]:
            song_queue[guild_id] = []
            await interaction.response.send_message("The queue has been cleared.")
        else:
            await interaction.response.send_message("The queue is currently empty, nothing to clear.")

    @bot.tree.command(name="skip", description="Skip the currently playing song")
    async def skip(interaction: discord.Interaction):
        await interaction.response.defer()

        guild_id = interaction.guild.id
        if guild_id in voice_clients:
            voice_client = voice_clients[guild_id]
            if voice_client.is_playing():
                voice_client.stop()  # Stop the current song
                await play_next(interaction)  # Play the next song in the queue
                await interaction.followup.send("Skipped to the next song.")
            else:
                await interaction.followup.send("No song is currently playing.")
        else:
            await interaction.followup.send("Not connected to a voice channel.")

    @bot.tree.command(name="shuffle", description="Shuffle the current song queue")
    async def shuffle(interaction: discord.Interaction):
        guild_id = interaction.guild.id
        if guild_id in song_queue and song_queue[guild_id]:
            random.shuffle(song_queue[guild_id])
            await interaction.response.send_message("The queue has been shuffled.")
        else:
            await interaction.response.send_message("The queue is currently empty, nothing to shuffle.")

    @bot.tree.command(name="loop", description="Toggle loop for the current song")
    async def loop(interaction: discord.Interaction):
        guild_id = interaction.guild.id
        loop_status[guild_id] = not loop_status.get(guild_id, False)
        status = "enabled" if loop_status[guild_id] else "disabled"
        await interaction.response.send_message(f"Looping is now {status}.")

    @bot.tree.command(name="search", description="Search for a song on YouTube")
    async def search(interaction: discord.Interaction, query: str):
        try:
            query_string = urllib.parse.urlencode({"search_query": query})
            html_content = urllib.request.urlopen(yt_results_url + query_string)
            search_results = re.findall(r'/watch\?v=(.{11})', html_content.read().decode())

            if not search_results:
                await interaction.response.send_message("No results found.")
                return
            
            await interaction.response.send_message("Search results:\n" + yt_watch_url + search_results[0])
        except Exception as e:
            print(f"An error occurred in search: {e}")
            await interaction.response.send_message("Something went wrong while trying to search for the song.")

    def _search_url(query: str):
        query_string = urllib.parse.urlencode({"search_query": query})
        html_content = urllib.request.urlopen(yt_results_url + query_string)
        search_results = re.findall(r'/watch\?v=(.{11})', html_content.read().decode())

        if not search_results:
            return None

        return yt_watch_url + search_results[0]

    bot.run(TOKEN)

if __name__ == "__main__":
    run_bot()
