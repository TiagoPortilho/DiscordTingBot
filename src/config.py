import os
from dotenv import load_dotenv
from discord.ext import commands
import discord
import yt_dlp

# Carrega variáveis de ambiente
load_dotenv()

# Configurações (valores padrão, podem ser sobrescritos via .env)
DISCORD_API_KEY = os.getenv("DISCORD_API_KEY")
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "$")
TTS_LANG = os.getenv("TTS_LANG", "pt")
PITCH_FACTOR = float(os.getenv("PITCH_FACTOR", "0.85"))
JOKENPO_TIMEOUT = int(os.getenv("JOKENPO_TIMEOUT", "30"))

# Constantes
DESCRIPTION = "Discord Bot com comandos e TTS"
EMOJIS_JOKENPO = {"🪨": "Pedra", "📄": "Papel", "✂️": "Tesoura"}
FFMPEG_EXECUTABLE = "ffmpeg"
TTS_FILES = ('tts_output.mp3', 'tts_output_male.mp3')

# Configurações para música
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

# Inicializa objetos globais
ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

# Intents necessários
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# Inicializa o bot
bot = commands.Bot(command_prefix=COMMAND_PREFIX, description=DESCRIPTION, intents=intents)