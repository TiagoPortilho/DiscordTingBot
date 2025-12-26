# TingBot

A Discord bot built with Python using discord.py.

## Features

- Greeting command: `$ola`
- Dice roll: `$dado <max>`
- Rock-Paper-Scissors: `$jokenpo`
- Text-to-Speech: `$falar <text>` (requires FFmpeg) – Optional: `$falar <text> | <pitch>` to adjust voice depth (e.g., 0.8 for deeper)

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

## Requirements

- Python 3.8+ (for local setup)
- FFmpeg (included in Docker)
- Docker (optional, for containerized setup)

## License

[Add license if applicable]
