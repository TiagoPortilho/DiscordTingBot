import discord
import random
import os
from dotenv import load_dotenv
from discord.ext import commands
from gtts import gTTS
import asyncio
import subprocess
import yt_dlp
import urllib.parse
import re
from collections import deque

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

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

# Intents necessários
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# Inicializa o bot
bot = commands.Bot(command_prefix=COMMAND_PREFIX, description=DESCRIPTION, intents=intents)

# Classes para música
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.duration = data.get('duration')
        self.thumbnail = data.get('thumbnail')
        self.uploader = data.get('uploader')
        self.webpage_url = data.get('webpage_url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        
        if 'entries' in data:
            data = data['entries'][0]
        
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS), data=data)

class MusicBot:
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}
        self.current = {}
        self.loop_mode = {}
        
    def get_queue(self, guild_id):
        if guild_id not in self.queues:
            self.queues[guild_id] = deque()
        return self.queues[guild_id]
    
    def get_current(self, guild_id):
        return self.current.get(guild_id)
    
    def set_current(self, guild_id, source):
        self.current[guild_id] = source
    
    def clear_current(self, guild_id):
        if guild_id in self.current:
            del self.current[guild_id]
    
    def get_loop_mode(self, guild_id):
        return self.loop_mode.get(guild_id, False)
    
    def toggle_loop(self, guild_id):
        self.loop_mode[guild_id] = not self.loop_mode.get(guild_id, False)
        return self.loop_mode[guild_id]

music_bot = MusicBot(bot)

# Função auxiliar para conectar ao voice channel
async def connect_to_voice(ctx):
    if ctx.author.voice is None:
        embed = discord.Embed(title="❌ Erro", description="Você precisa estar em um canal de voz para usar este comando.", color=discord.Color.red())
        await ctx.send(embed=embed)
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
    embed = discord.Embed(title="🏓 Pong!", description=f"Latência: **{round(bot.latency * 1000)}ms**", color=discord.Color.green())
    await ctx.reply(embed=embed, mention_author=True)


@bot.command(name="sair", help="Faz o bot sair do canal de voz.")
async def sair(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        embed = discord.Embed(title="👋 Tchau!", description="Saí do canal de voz!", color=discord.Color.orange())
        await ctx.reply(embed=embed, mention_author=True)
    else:
        embed = discord.Embed(title="❌ Erro", description="Não estou em nenhum canal de voz.", color=discord.Color.red())
        await ctx.reply(embed=embed, mention_author=True)


@bot.command(name="dado", help="Rola um dado de 1 até o número máximo especificado.")
async def dado(ctx, dmax: str):
    try:
        max_val = int(dmax)
        if max_val < 1:
            embed = discord.Embed(title="❌ Erro", description="O número máximo deve ser pelo menos 1.", color=discord.Color.red())
            await ctx.reply(embed=embed, mention_author=True)
        else:
            resultado = random.randint(1, max_val)
            embed = discord.Embed(title="🎲 Dado Rolado!", description=f"**{resultado}** (1-{max_val})", color=discord.Color.blue())
            await ctx.reply(embed=embed, mention_author=True)
    except ValueError:
        embed = discord.Embed(title="❌ Erro", description="Por favor, forneça um número válido.", color=discord.Color.red())
        await ctx.reply(embed=embed, mention_author=True)


@bot.command(name="jokenpo", help="Joga pedra, papel e tesoura com o bot.")
async def jokenpo(ctx):
    embed = discord.Embed(title="🎮 Jokenpô!", description="Vamos jogar pedra, papel e tesoura?\nEscolha uma opção reagindo com um dos emojis abaixo:", color=discord.Color.purple())
    msg = await ctx.send(embed=embed)

    for emoji in EMOJIS_JOKENPO:
        await msg.add_reaction(emoji)

    emoji_to_num = {"🪨": 1, "📄": 2, "✂️": 3}
    botchoice = random.randint(1, 3)

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in EMOJIS_JOKENPO and reaction.message.id == msg.id

    try:
        reaction, user = await bot.wait_for("reaction_add", check=check, timeout=JOKENPO_TIMEOUT)
    except asyncio.TimeoutError:
        embed = discord.Embed(title="⏰ Tempo Esgotado", description="Você demorou muito para reagir!", color=discord.Color.red())
        await ctx.send(embed=embed)
        return

    userchoice = emoji_to_num[str(reaction.emoji)]
    bot_emoji = {1: "🪨", 2: "📄", 3: "✂️"}[botchoice]

    # Determina o resultado e cor
    if userchoice == botchoice:
        result = f"{user.mention} nós empatamos!"
        result_color = discord.Color.yellow()
        title = "🤝 Empate!"
    elif (userchoice - botchoice) % 3 == 1:
        result = f"Parabéns {user.mention} você venceu!"
        result_color = discord.Color.green()
        title = "🎉 Vitória!"
    else:
        result = f"HAHAHA {user.mention} você perdeu pra um robô!"
        result_color = discord.Color.red()
        title = "🤖 Derrota!"

    embed = discord.Embed(title=title, color=result_color)
    embed.add_field(name="Você escolheu:", value=f"{EMOJIS_JOKENPO[str(reaction.emoji)]} {str(reaction.emoji)}", inline=True)
    embed.add_field(name="Eu escolhi:", value=f"{EMOJIS_JOKENPO[bot_emoji]} {bot_emoji}", inline=True)
    embed.add_field(name="Resultado:", value=result, inline=False)
    await ctx.send(embed=embed)


@bot.command(name='falar', help="Fala o texto fornecido em um canal de voz usando TTS. Opcional: | <pitch> para ajustar profundidade da voz (ex: 0.8 para mais grave; padrão usa 0.85).")
async def falar(ctx, *, texto_and_pitch: str):
    vc = await connect_to_voice(ctx)
    if vc is None:
        return

    try:
        texto, pitch = parse_texto_and_pitch(texto_and_pitch)
    except ValueError as e:
        embed = discord.Embed(title="❌ Erro", description=str(e), color=discord.Color.red())
        await ctx.send(embed=embed)
        return

    play_file = generate_tts_audio(texto, pitch)

    def after_playing(error):
        if error:
            print(f"Erro ao reproduzir o áudio: {error}")
        cleanup_tts_files()

    vc.play(discord.FFmpegPCMAudio(play_file, executable=FFMPEG_EXECUTABLE), after=after_playing)
    
    # Enviar confirmação com embed
    embed = discord.Embed(title="🗣️ TTS Ativo", description=f"Falando: **{texto[:100]}{'...' if len(texto) > 100 else ''}**", color=discord.Color.blue())
    if pitch != 1.0:
        embed.add_field(name="Pitch", value=f"{pitch}x", inline=True)
    await ctx.send(embed=embed)


# Comandos de música
async def play_next(ctx):
    guild_id = ctx.guild.id
    queue = music_bot.get_queue(guild_id)
    
    if queue:
        next_source = queue.popleft()
        music_bot.set_current(guild_id, next_source)
        
        def after_playing(error):
            if error:
                print(f'Player error: {error}')
            
            # Se o loop estiver ativado, recolocar a música na fila
            if music_bot.get_loop_mode(guild_id):
                current = music_bot.get_current(guild_id)
                if current:
                    queue.appendleft(current)
            
            music_bot.clear_current(guild_id)
            
            # Tocar próxima música
            asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
        
        ctx.voice_client.play(next_source, after=after_playing)
        await ctx.send(f'🎵 Tocando agora: **{next_source.title}**')
    else:
        music_bot.clear_current(guild_id)
        await ctx.send('📭 A fila de música está vazia!')

@bot.command(name='tocar', aliases=['play', 'p'], help='Toca uma música do YouTube. Use: $tocar <nome da música ou URL>')
async def tocar(ctx, *, url):
    vc = await connect_to_voice(ctx)
    if vc is None:
        return
    
    async with ctx.typing():
        try:
            # Verificar se é uma URL direta ou busca
            if not (url.startswith('http://') or url.startswith('https://')):
                # É uma busca, então fazer busca no YouTube
                url = f"ytsearch:{url}"
            
            source = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
            guild_id = ctx.guild.id
            queue = music_bot.get_queue(guild_id)
            
            if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
                queue.append(source)
                embed = discord.Embed(title="📝 Adicionado à Fila", description=f"**{source.title}**", color=discord.Color.blue())
                embed.add_field(name="Posição na fila", value=f"#{len(queue)}", inline=True)
                if source.duration:
                    minutes, seconds = divmod(source.duration, 60)
                    embed.add_field(name="Duração", value=f"{int(minutes):02d}:{int(seconds):02d}", inline=True)
                if source.thumbnail:
                    embed.set_thumbnail(url=source.thumbnail)
                if source.uploader:
                    embed.set_footer(text=f"Por: {source.uploader}")
                await ctx.send(embed=embed)
            else:
                music_bot.set_current(guild_id, source)
                
                def after_playing(error):
                    if error:
                        print(f'Player error: {error}')
                    
                    # Se o loop estiver ativado, recolocar a música na fila
                    if music_bot.get_loop_mode(guild_id):
                        current = music_bot.get_current(guild_id)
                        if current:
                            queue.appendleft(current)
                    
                    music_bot.clear_current(guild_id)
                    
                    # Tocar próxima música
                    asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
                
                ctx.voice_client.play(source, after=after_playing)
                
                embed = discord.Embed(title="🎵 Tocando Agora", description=f"**{source.title}**", color=discord.Color.green())
                if source.duration:
                    minutes, seconds = divmod(source.duration, 60)
                    embed.add_field(name="Duração", value=f"{int(minutes):02d}:{int(seconds):02d}", inline=True)
                if source.thumbnail:
                    embed.set_thumbnail(url=source.thumbnail)
                if source.uploader:
                    embed.set_footer(text=f"Por: {source.uploader}")
                if source.webpage_url:
                    embed.add_field(name="Link", value=f"[YouTube]({source.webpage_url})", inline=True)
                
                await ctx.send(embed=embed)
                
        except Exception as e:
            embed = discord.Embed(title="❌ Erro", description=f"Erro ao tentar tocar a música: {str(e)}", color=discord.Color.red())
            await ctx.send(embed=embed)

@bot.command(name='pausar', aliases=['pause'], help='Pausa a música atual')
async def pausar(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        embed = discord.Embed(title="⏸️ Música Pausada", description="A música foi pausada com sucesso!", color=discord.Color.orange())
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="❌ Erro", description="Não há música tocando no momento.", color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(name='continuar', aliases=['resume', 'despausar'], help='Continua a música pausada')
async def continuar(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        embed = discord.Embed(title="▶️ Música Retomada", description="A música foi retomada com sucesso!", color=discord.Color.green())
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="❌ Erro", description="Não há música pausada no momento.", color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(name='parar', aliases=['stop'], help='Para a música e limpa a fila')
async def parar(ctx):
    if ctx.voice_client:
        guild_id = ctx.guild.id
        music_bot.get_queue(guild_id).clear()
        music_bot.clear_current(guild_id)
        ctx.voice_client.stop()
        embed = discord.Embed(title="⏹️ Música Parada", description="Música parada e fila limpa!", color=discord.Color.red())
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="❌ Erro", description="Não estou conectado a nenhum canal de voz.", color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(name='pular', aliases=['skip', 'next'], help='Pula para a próxima música na fila')
async def pular(ctx):
    if ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
        ctx.voice_client.stop()
        embed = discord.Embed(title="⏭️ Música Pulada", description="Pulando para a próxima música...", color=discord.Color.blue())
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="❌ Erro", description="Não há música tocando no momento.", color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(name='fila', aliases=['queue', 'q'], help='Mostra as próximas músicas na fila')
async def fila(ctx):
    guild_id = ctx.guild.id
    queue = music_bot.get_queue(guild_id)
    current = music_bot.get_current(guild_id)
    
    if not current and not queue:
        await ctx.send('📭 A fila está vazia!')
        return
    
    embed = discord.Embed(title='🎵 Fila de Música', color=discord.Color.blue())
    
    if current:
        embed.add_field(name='🎵 Tocando Agora', value=f'**{current.title}**', inline=False)
    
    if queue:
        queue_text = ""
        for i, source in enumerate(list(queue)[:10]):  # Mostra apenas as próximas 10
            queue_text += f'{i+1}. **{source.title}**\n'
        
        if len(queue) > 10:
            queue_text += f'\n... e mais {len(queue) - 10} músicas'
        
        embed.add_field(name='📝 Próximas na Fila', value=queue_text, inline=False)
    
    embed.set_footer(text=f'Total na fila: {len(queue)} | Loop: {"✅" if music_bot.get_loop_mode(guild_id) else "❌"}')
    await ctx.send(embed=embed)

@bot.command(name='loop', aliases=['repetir'], help='Ativa/desativa o modo loop da música atual')
async def loop(ctx):
    guild_id = ctx.guild.id
    loop_status = music_bot.toggle_loop(guild_id)
    
    if loop_status:
        embed = discord.Embed(title="🔄 Loop Ativado", description="A música atual será repetida indefinidamente!", color=discord.Color.green())
    else:
        embed = discord.Embed(title="❌ Loop Desativado", description="A reprodução voltará ao modo normal.", color=discord.Color.orange())
    
    await ctx.send(embed=embed)

@bot.command(name='volume', aliases=['vol'], help='Ajusta o volume da música (0-100)')
async def volume(ctx, volume: int = None):
    if volume is None:
        current = music_bot.get_current(ctx.guild.id)
        if current and hasattr(current, 'volume'):
            embed = discord.Embed(title="🔊 Volume Atual", description=f"Volume: **{int(current.volume * 100)}%**", color=discord.Color.blue())
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="❌ Erro", description="Não há música tocando no momento.", color=discord.Color.red())
            await ctx.send(embed=embed)
        return
    
    if not 0 <= volume <= 100:
        embed = discord.Embed(title="❌ Erro", description="Volume deve estar entre 0 e 100!", color=discord.Color.red())
        await ctx.send(embed=embed)
        return
    
    current = music_bot.get_current(ctx.guild.id)
    if current and hasattr(current, 'volume'):
        current.volume = volume / 100
        embed = discord.Embed(title="🔊 Volume Ajustado", description=f"Volume ajustado para **{volume}%**", color=discord.Color.green())
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="❌ Erro", description="Não há música tocando no momento.", color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command(name='tocando', aliases=['np', 'nowplaying'], help='Mostra informações sobre a música atual')
async def tocando(ctx):
    current = music_bot.get_current(ctx.guild.id)
    if current:
        embed = discord.Embed(title="🎵 Tocando Agora", color=discord.Color.green())
        embed.add_field(name="Título", value=f"**{current.title}**", inline=False)
        
        if current.duration:
            minutes, seconds = divmod(current.duration, 60)
            embed.add_field(name="Duração", value=f"{int(minutes):02d}:{int(seconds):02d}", inline=True)
        
        loop_status = "✅ Ativado" if music_bot.get_loop_mode(ctx.guild.id) else "❌ Desativado"
        embed.add_field(name="Loop", value=loop_status, inline=True)
        
        if hasattr(current, 'volume'):
            embed.add_field(name="Volume", value=f"{int(current.volume * 100)}%", inline=True)
        
        if current.thumbnail:
            embed.set_thumbnail(url=current.thumbnail)
        
        if current.uploader:
            embed.set_footer(text=f"Por: {current.uploader}")
        
        if current.webpage_url:
            embed.add_field(name="Link", value=f"[YouTube]({current.webpage_url})", inline=False)
        
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="❌ Nenhuma Música", description="Não há música tocando no momento.", color=discord.Color.red())
        await ctx.send(embed=embed)


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
