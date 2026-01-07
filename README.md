# TingBot

<p align="center">
  <img src="img/tingbotProfile.webp" alt="TingBot Logo" width="150">
</p>

TingBot is a Python Discord bot featuring YouTube music playback, text-to-speech functionality, interactive games, and bilingual command support with simultaneous audio capabilities.

##  Technologies

<p align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Discord.py-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Discord.py">
  <img src="https://img.shields.io/badge/yt--dlp-FF0000?style=for-the-badge&logo=youtube&logoColor=white" alt="yt-dlp">
  <img src="https://img.shields.io/badge/gTTS-4285F4?style=for-the-badge&logo=google&logoColor=white" alt="gTTS">
  <img src="https://img.shields.io/badge/FFmpeg-007808?style=for-the-badge&logo=ffmpeg&logoColor=white" alt="FFmpeg">
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
</p>

## Features

- **Basic Commands**: `$ping`, `$help` / `$ajuda`
- **Voice Control**: `$sair` / `$exit` (leave voice channel)
- **Games**: `$dado` / `$dice <max>` (dice roll), `$jokenpo` / `$rps` (rock-paper-scissors)
- **Text-to-Speech**: `$falar` / `$speak <text>` with optional pitch control (`$falar <text> | <pitch>`)
- **TTS Queue**: `$tts_fila` / `$tts_queue` (view TTS queue)
- **Music Player**: 
  - `$tocar` / `$play <song/URL>` (play YouTube music)
  - `$pausar` / `$pause`, `$continuar` / `$resume`, `$parar` / `$stop`
  - `$pular` / `$skip`, `$fila` / `$queue`, `$loop` / `$repetir`
  - `$volume` / `$vol <0-100>`, `$tocando` / `$np` (now playing)
- **Simultaneous Audio**: TTS works alongside music playback

## Setup

### Option 1: Local Setup

1. Clone the repository.
2. Create a virtual environment: `python -m venv .venv`
3. Activate the virtual environment: `.venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and add your Discord API key: `DISCORD_API_KEY=your_key_here`
6. Download FFmpeg from https://ffmpeg.org and add `ffmpeg/bin` to your PATH for voice commands.
7. Run the bot: `python tingbot.py`

### Option 2: Docker Setup (Recommended)

Docker simplifies the setup by including FFmpeg automatically.

1. Ensure Docker and Docker Compose are installed on your system.
2. Clone the repository.
3. Copy `.env.example` to `.env` and add your Discord API key: `DISCORD_API_KEY=your_key_here`
   - Optionally, configure other settings:
     - `COMMAND_PREFIX`: Bot command prefix (default: $)
     - `TTS_LANG`: Language for TTS (default: pt)
     - `PITCH_FACTOR`: Factor for voice pitch shift (0.8-0.9 for deeper voice, default: 0.85)
     - `JOKENPO_TIMEOUT`: Timeout in seconds for jokenpo reactions (default: 30)
4. Build and run with Docker Compose: `docker-compose up --build`

This will build the image and start the container with the environment variables from `.env`.

For voice features to work in Docker, ensure the container has access to audio devices if running locally (may require additional flags like `--device /dev/snd` on Linux).

## Usage

Use `$help` or `$ajuda` for a complete list of commands. All commands work in Portuguese and English.

**Quick Start:**
- Join a voice channel
- `$tocar never gonna give you up` (plays music)
- `$falar olá mundo` (TTS while music plays)
- `$help` (shows all commands)

## Requirements

- Python 3.8+ (for local setup)
- FFmpeg (included in Docker)
- Docker (optional, for containerized setup)
- Dependencies: discord.py, yt-dlp, gtts, python-dotenv

## License

MIT License
