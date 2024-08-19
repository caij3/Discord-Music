import discord
import os
import asyncio
import yt_dlp
from dotenv import load_dotenv

def run_bot():
    load_dotenv()
    TOKEN = os.getenv('TOKEN')
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    voice_clients = {}
    yt_dlp_options = {"format": "bestaudio/best"}
    ytdl = yt_dlp.YoutubeDL(yt_dlp_options)

    ffmpeg_options = {'options': '-vn'}

    @client.event
    async def on_ready():
        print(f'{client.user} has connected to Discord!')

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return

        if message.content.startswith('!play'):
            try:
                # Join the voice channel if not already connected
                if message.guild.id not in voice_clients:
                    if message.author.voice:
                        channel = message.author.voice.channel
                        voice_client = await channel.connect()
                        voice_clients[message.guild.id] = voice_client
                    else:
                        await message.channel.send("You are not connected to a voice channel.")
                        return
                else:
                    voice_client = voice_clients[message.guild.id]

                url = message.content.split()[1]

                # Use an executor to run the yt_dlp blocking code
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))

                song = data['url']
                player = discord.FFmpegPCMAudio(song, **ffmpeg_options)

                # Check if already playing
                if not voice_client.is_playing():
                    voice_client.play(player)
                else:
                    await message.channel.send("Already playing a song!")
            except Exception as e:
                print(f"An error occurred: {e}")
                await message.channel.send("Something went wrong while trying to play the song.")

        if message.content.startswith('!pause'):
            try:
                if message.guild.id in voice_clients:
                    voice_client = voice_clients[message.guild.id]
                    if voice_client.is_playing():
                        voice_client.pause()
                    else:
                        await message.channel.send("No song is currently playing.")
                else:
                    await message.channel.send("Not connected to a voice channel.")
            except Exception as e:
                print(f"An error occurred: {e}")
                await message.channel.send("Something went wrong while trying to pausing the song.")

        if message.content.startswith('!resume'):
            try:
                if message.guild.id in voice_clients:
                    voice_client = voice_clients[message.guild.id]
                    if voice_client.is_paused():
                        voice_client.resume()
                    else:
                        await message.channel.send("No song is currently paused.")
                else:
                    await message.channel.send("Not connected to a voice channel.")
            except Exception as e:
                print(f"An error occurred: {e}")
                await message.channel.send("Something went wrong while trying to resuming the song.")
        
        if message.content.startswith('!stop'):
            try:
                if message.guild.id in voice_clients:
                    voice_client = voice_clients[message.guild.id]
                    voice_client.stop()
                else:
                    await message.channel.send("Not connected to a voice channel.")
            except Exception as e:
                print(f"An error occurred: {e}")
                await message.channel.send("Something went wrong while trying to stop the song.")


    client.run(TOKEN)
