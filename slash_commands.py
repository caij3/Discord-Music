import discord
import os
import asyncio
import yt_dlp
import random
from dotenv import load_dotenv
from discord.ext import commands

def run_bot():
    load_dotenv()
    TOKEN = os.getenv('TOKEN')
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix='!', intents=intents)

    voice_clients = {}
    song_queues = {}
    current_songs = {}
    yt_dlp_options = {"format": "bestaudio/best"}
    ytdl = yt_dlp.YoutubeDL(yt_dlp_options)

    ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                      'options': '-vn -af "volume=0.25"'}

    async def play_next(interaction: discord.Interaction):
        guild_id = interaction.guild.id
        if guild_id in song_queues and song_queues[guild_id]:
            url = song_queues[guild_id].pop(0)
            try:
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
                title = data.get('title', 'Unknown Title')

                voice_client = voice_clients[guild_id]
                player = discord.FFmpegOpusAudio(data['url'], **ffmpeg_options)

                def on_song_end(error):
                    if error:
                        print(f"An error occurred while playing the song: {error}")
                    # leave voice channel if queue is empty
                    if not song_queues[guild_id]:
                        # leave voice channel if queue is empty
                        loop.call_soon_threadsafe(lambda: asyncio.create_task(voice_client.disconnect()))
                        del voice_clients[guild_id]
                        del song_queues[guild_id]
                        del current_songs[guild_id]
                    else:
                        # Schedule the next song to play
                        loop.call_soon_threadsafe(lambda: asyncio.create_task(play_next(interaction)))

                if voice_client.is_playing():
                    voice_client.stop()

                voice_client.play(player, after=on_song_end)
                current_songs[guild_id] = title
                await interaction.followup.send(f"Now playing: {title}")

            except Exception as e:
                print(f"An error occurred: {e}")
                await interaction.followup.send("Failed to play the song.")
        else:
            await interaction.followup.send("The queue is empty.")

    @bot.event
    async def on_ready():
        print(f'{bot.user} has connected to Discord!')
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands.")

    @bot.tree.command(name="play", description="Play a song from a URL")
    async def play(interaction: discord.Interaction, url: str):
        print("Play initiated")
        await interaction.response.defer()

        guild_id = interaction.guild.id
        if guild_id not in voice_clients:
            if interaction.user.voice:
                channel = interaction.user.voice.channel
                voice_client = await channel.connect()
                await voice_client.guild.change_voice_state(channel=channel, self_deaf=True)
                voice_clients[guild_id] = voice_client
                song_queues[guild_id] = []
            else:
                await interaction.followup.send("You are not connected to a voice channel.")
                return
        else:
            voice_client = voice_clients[guild_id]

        try:
            song_queues[guild_id].append(url)
            if not voice_client.is_playing():
                await play_next(interaction)
            else:
                await interaction.followup.send("Song added to queue.")

        except Exception as e:
            print(f"An error occurred: {e}")
            await interaction.followup.send("Something went wrong while trying to play the song.")

    @bot.tree.command(name="playing", description="Show the currently playing song")
    async def playing(interaction: discord.Interaction):
        guild_id = interaction.guild.id
        if guild_id in current_songs and current_songs[guild_id]:
            await interaction.response.send_message(f"Currently playing: {current_songs[guild_id]}")
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
            print(f"An error occurred: {e}")
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
            print(f"An error occurred: {e}")
            await interaction.response.send_message("Something went wrong while trying to resume the song.")

    @bot.tree.command(name="stop", description="Stop the current song")
    async def stop(interaction: discord.Interaction):
        try:
            if interaction.guild.id in voice_clients:
                voice_client = voice_clients[interaction.guild.id]
                voice_client.stop()
                song_queues[interaction.guild.id] = []  # Clear the queue
                await interaction.response.send_message("Song stopped and queue cleared.")
            else:
                await interaction.response.send_message("Not connected to a voice channel.")
        except Exception as e:
            print(f"An error occurred: {e}")
            await interaction.response.send_message("Something went wrong while trying to stop the song.")

    @bot.tree.command(name="leave", description="Make the bot leave")
    async def leave(interaction: discord.Interaction):
        try:
            if interaction.guild.id in voice_clients:
                voice_client = voice_clients[interaction.guild.id]
                await voice_client.disconnect()
                del voice_clients[interaction.guild.id]
                del song_queues[interaction.guild.id]
                await interaction.response.send_message("Left the voice channel.")
            else:
                await interaction.response.send_message("Not connected to a voice channel.")
        except Exception as e:
            print(f"An error occurred: {e}")
            await interaction.response.send_message("Something went wrong while trying to leave the voice channel.")

    @bot.tree.command(name="queue", description="View the current song queue")
    async def queue(interaction: discord.Interaction):
        guild_id = interaction.guild.id
        if guild_id in song_queues and song_queues[guild_id]:
            queue_list = song_queues[guild_id]
            queue_str = "\n".join([f"{i + 1}. {url}" for i, url in enumerate(queue_list)])
            await interaction.response.send_message(f"Current queue:\n{queue_str}")
        else:
            await interaction.response.send_message("The queue is currently empty.")

    # todo: fix skip to not skip to last song
    @bot.tree.command(name="skip", description="Skip the currently playing song")
    async def skip(interaction: discord.Interaction):
        await interaction.response.defer()

        guild_id = interaction.guild.id
        if guild_id in voice_clients:
            voice_client = voice_clients[guild_id]
            if voice_client.is_playing():
                voice_client.stop()  # Stop the current song
                await play_next(interaction)  # Pass the interaction here
                await interaction.followup.send("Skipped to the next song.")
            else:
                await interaction.followup.send("No song is currently playing.")
        else:
            await interaction.followup.send("Not connected to a voice channel.")

    @bot.tree.command(name="shuffle", description="Shuffle the current song queue")
    async def shuffle(interaction: discord.Interaction):
        guild_id = interaction.guild.id
        if guild_id in song_queues and song_queues[guild_id]:
            random.shuffle(song_queues[guild_id])
            await interaction.response.send_message("The queue has been shuffled.")
        else:
            await interaction.response.send_message("The queue is currently empty, nothing to shuffle.")

    bot.run(TOKEN)

if __name__ == "__main__":
    run_bot()
