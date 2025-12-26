import discord
import random
import os
from dotenv import load_dotenv
from discord.ext import commands
from gtts import gTTS
import asyncio
import subprocess

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

# Intents necessários
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# Inicializa o bot
bot = commands.Bot(command_prefix=COMMAND_PREFIX, description=DESCRIPTION, intents=intents)

# Função auxiliar para conectar ao voice channel
async def connect_to_voice(ctx):
    if ctx.author.voice is None:
        await ctx.send("Você precisa estar em um canal de voz para usar este comando.")
        return None
    voice_channel = ctx.author.voice.channel
    if ctx.voice_client is None:
        vc = await voice_channel.connect()
    else:
        vc = ctx.voice_client
        if vc.channel != voice_channel:
            await vc.move_to(voice_channel)
    return vc

# Função auxiliar para parsear texto e pitch
def parse_texto_and_pitch(texto_and_pitch):
    if "|" in texto_and_pitch:
        texto, pitch_str = texto_and_pitch.rsplit("|", 1)
        texto = texto.strip()
        pitch_str = pitch_str.strip()
        if pitch_str == "":
            pitch = PITCH_FACTOR
        else:
            try:
                pitch = float(pitch_str)
            except ValueError:
                raise ValueError("Pitch inválido. Use um número como 0.85.")
    else:
        texto = texto_and_pitch.strip()
        pitch = PITCH_FACTOR
    return texto, pitch

# Função auxiliar para gerar e processar TTS
def generate_tts_audio(texto, pitch):
    tts = gTTS(texto, lang=TTS_LANG)
    tts.save('tts_output.mp3')
    play_file = 'tts_output.mp3'
    if pitch != 1.0:
        try:
            subprocess.run([
                FFMPEG_EXECUTABLE, '-y', '-i', 'tts_output.mp3',
                '-filter:a', f'asetrate=44100*{pitch},aresample=44100,atempo=1.0', 'tts_output_male.mp3'
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            play_file = 'tts_output_male.mp3'
        except Exception as e:
            print(f'FFmpeg pitch shift failed: {e} — falling back to original gTTS output')
    return play_file

# Função auxiliar para limpar arquivos TTS
def cleanup_tts_files():
    for f in TTS_FILES:
        try:
            if os.path.exists(f):
                os.remove(f)
        except Exception:
            pass
    print('Arquivos TTS removidos.')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')


@bot.command(name="ping", help="Verifica a latência do bot.")
async def ping(ctx):
    await ctx.reply(f"Pong! Latência: {round(bot.latency * 1000)}ms", mention_author=True)


@bot.command(name="sair", help="Faz o bot sair do canal de voz.")
async def sair(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.reply("Saí do canal de voz!", mention_author=True)
    else:
        await ctx.reply("Não estou em nenhum canal de voz.", mention_author=True)


@bot.command(name="dado", help="Rola um dado de 1 até o número máximo especificado.")
async def dado(ctx, dmax: str):
    try:
        max_val = int(dmax)
        if max_val < 1:
            await ctx.reply("O número máximo deve ser pelo menos 1.", mention_author=True)
        else:
            await ctx.reply(random.randint(1, max_val), mention_author=True)
    except ValueError:
        await ctx.reply("Por favor, forneça um número válido.", mention_author=True)


@bot.command(name="jokenpo", help="Joga pedra, papel e tesoura com o bot.")
async def jokenpo(ctx):
    msg = await ctx.send("Vamos jogar pedra, papel e tesoura?\nEscolha uma opção reagindo com um dos emojis abaixo:")

    for emoji in EMOJIS_JOKENPO:
        await msg.add_reaction(emoji)

    emoji_to_num = {"🪨": 1, "📄": 2, "✂️": 3}
    botchoice = random.randint(1, 3)

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in EMOJIS_JOKENPO and reaction.message.id == msg.id

    try:
        reaction, user = await bot.wait_for("reaction_add", check=check, timeout=JOKENPO_TIMEOUT)
    except asyncio.TimeoutError:
        await ctx.send("Você demorou muito para reagir!")
        return

    userchoice = emoji_to_num[str(reaction.emoji)]
    bot_emoji = {1: "🪨", 2: "📄", 3: "✂️"}[botchoice]

    # Determina o resultado
    if userchoice == botchoice:
        result = f"{user.mention} nós empatamos!"
    elif (userchoice - botchoice) % 3 == 1:
        result = f"Parabéns {user.mention} você venceu!"
    else:
        result = f"HAHAHA {user.mention} você perdeu pra um robô!"

    await ctx.send(f"Você escolheu: {EMOJIS_JOKENPO[str(reaction.emoji)]} {str(reaction.emoji)}\nEu escolhi: {EMOJIS_JOKENPO[bot_emoji]} {bot_emoji}")
    await ctx.send(result)


@bot.command(name='falar', help="Fala o texto fornecido em um canal de voz usando TTS. Opcional: | <pitch> para ajustar profundidade da voz (ex: 0.8 para mais grave; padrão usa 0.85).")
async def falar(ctx, *, texto_and_pitch: str):
    vc = await connect_to_voice(ctx)
    if vc is None:
        return

    try:
        texto, pitch = parse_texto_and_pitch(texto_and_pitch)
    except ValueError as e:
        await ctx.send(str(e))
        return

    play_file = generate_tts_audio(texto, pitch)

    def after_playing(error):
        if error:
            print(f"Erro ao reproduzir o áudio: {error}")
        cleanup_tts_files()

    vc.play(discord.FFmpegPCMAudio(play_file, executable=FFMPEG_EXECUTABLE), after=after_playing)


class MyHelp(commands.HelpCommand):
    def get_command_signature(self, command):
        return '%s%s %s' % (self.context.clean_prefix, command.qualified_name, command.signature)

    async def send_bot_help(self, mapping):
        embed = discord.Embed(title="Help", color=discord.Color.green())
        for cog, cmmds in mapping.items():
            filtered = await self.filter_commands(cmmds, sort=True)
            if command_signatures := [
                self.get_command_signature(c) for c in filtered
            ]:
                cog_name = getattr(cog, "qualified_name", "Comandos")
                embed.add_field(name=cog_name, value="\n".join(command_signatures), inline=False)

        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_command_help(self, command):
        embed = discord.Embed(title=self.get_command_signature(command), color=discord.Color.green())
        if command.help:
            embed.description = command.help
        if alias := command.aliases:
            embed.add_field(name="Aliases", value=", ".join(alias), inline=False)

        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_help_embed(self, title, dscrpt, cmmds):
        embed = discord.Embed(title=title, description=dscrpt or "No help found...")

        if filtered_commands := await self.filter_commands(cmmds):
            for command in filtered_commands:
                embed.add_field(name=self.get_command_signature(command), value=command.help or "No help found...")

        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog):
        title = cog.qualified_name or "No"
        await self.send_help_embed(f'{title} Category', cog.description, cog.get_commands())

    async def send_error_message(self, error):
        embed = discord.Embed(title="Error", description=error, color=discord.Color.red())
        channel = self.get_destination()
        await channel.send(embed=embed)


bot.help_command = MyHelp()

bot.run(DISCORD_API_KEY)
