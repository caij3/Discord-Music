***Disclaimer***<br>
This code is for educational purposes ONLY. Anything produced using this code should respect Discord and YouTube guidelines on streaming and downloading videos. Bots made using this code are not to be distributed, both non-commercially and commercially.

# Discord Music Bot

This is a simple yet feature-rich music bot for Discord built using Python and the `discord.py` library, along with `yt-dlp` for YouTube video/audio extraction. The bot allows users to play songs from YouTube, manage a queue, skip, pause, and resume songs, shuffle the queue, and more!

## Features

- **Play music** from YouTube links or search directly for songs on YouTube.
- **Queue management**: Add songs to the queue, view the queue, and remove songs from the queue.
- **Control playback**: Pause, resume, stop, and skip songs.
- **Loop and repeat**: Toggle repeat for the current song or enable/disable loop.
- **Shuffle** the queue to randomize the order of upcoming songs.
- **Search for songs** on YouTube directly from Discord.
- **Supports voice channels**: Join, leave, and manage voice channel connections.

## Requirements

- Python 3.8 or higher
- Install the necessary dependencies by running the following command:

```bash
pip install -r requirements.txt
```

You will need a .env file with your Discord bot token:
```bash
TOKEN=your-bot-token-here
```


## Setup

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/discord-music-bot.git cd discord-music-bot
```


### 2. Install dependencies

Make sure you have Python 3.8+ installed. Then, install the required dependencies:
```bash
pip install -r requirements.txt
```


### 3. Set up the `.env` file

Create a `.env` file in the root directory of the project and add your bot token:

```bash
TOKEN=your-discord-bot-token
```

You can get your bot token by creating a bot on the [Discord Developer Portal](https://discord.com/developers/applications).

### 4. Run the bot

Once everything is set up, run the bot with:
```bash
python bot.py
```


The bot should now be running and connected to your Discord server.

## Commands

Here are the available commands for the bot:

- `!play <url>`: Play a song from a YouTube URL.
- `!playing`: Show the currently playing song.
- `!pause`: Pause the current song.
- `!resume`: Resume the paused song.
- `!stop`: Stop the current song and clear the queue.
- `!leave`: Make the bot leave the voice channel.
- `!queue`: View the current song queue.
- `!clear`: Clear the song queue.
- `!remove <index>`: Remove a song from the queue by its index.
- `!skip`: Skip the currently playing song.
- `!shuffle`: Shuffle the song queue.
- `!repeat`: Toggle repeat for the current song.
- `!search <query>`: Search for a song on YouTube.

## Dependencies

- `discord.py`: A Python library for the Discord API.
- `yt-dlp`: A command-line program to download videos from YouTube and other platforms (successor to `youtube-dl`).
- `asyncio`: Used for asynchronous operations in Python.
- `python-dotenv`: To load environment variables from the `.env` file.
- `ffmpeg`: The bot requires `ffmpeg` to stream audio from YouTube links.

### Install `ffmpeg`:

- **Windows**: You can download `ffmpeg` from [here](https://ffmpeg.org/download.html). Make sure to add the `ffmpeg` bin folder to your system's PATH.
- **Linux**: Install `ffmpeg` via your package manager:

```bash
sudo apt install ffmpeg
```

## Notes

- Ensure that your bot has the necessary permissions to connect to voice channels and speak in them.
  - Scope: 
    - applications.commands
    - bot
  - Bot Permissions:
    - View Channels
    - Send Messages
    - Manage Messages
    - Use Slash Commands
    - Connect
    - Speak
- The bot uses `yt-dlp` to extract audio from YouTube links. If there are issues with specific videos, make sure `yt-dlp` is updated to the latest version.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
