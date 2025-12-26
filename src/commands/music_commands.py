import discord
import asyncio
from collections import deque
from src.config import ytdl, FFMPEG_OPTIONS, bot
from src.utils.utils import connect_to_voice

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

# Função auxiliar para tocar próxima música
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
        
        embed = discord.Embed(title="🎵 Tocando Agora", description=f"**{next_source.title}**", color=discord.Color.green())
        if next_source.thumbnail:
            embed.set_thumbnail(url=next_source.thumbnail)
        if next_source.uploader:
            embed.set_footer(text=f"Por: {next_source.uploader}")
        
        await ctx.send(embed=embed)
    else:
        music_bot.clear_current(guild_id)
        embed = discord.Embed(title="📝 Fila Vazia", description="A fila de música está vazia!", color=discord.Color.orange())
        await ctx.send(embed=embed)

# Comandos de música
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
        embed = discord.Embed(title="📝 Fila Vazia", description="A fila está vazia! Use `$tocar` para adicionar músicas.", color=discord.Color.orange())
        await ctx.send(embed=embed)
        return
    
    embed = discord.Embed(title="🎵 Fila de Música", color=discord.Color.blue())
    
    if current:
        duration_str = ""
        if current.duration:
            minutes, seconds = divmod(current.duration, 60)
            duration_str = f" ({int(minutes):02d}:{int(seconds):02d})"
        
        embed.add_field(name="🎵 Tocando Agora", value=f"**{current.title}**{duration_str}", inline=False)
        if current.thumbnail:
            embed.set_thumbnail(url=current.thumbnail)
    
    if queue:
        queue_text = ""
        for i, source in enumerate(list(queue)[:10]):  # Mostra apenas as próximas 10
            duration_str = ""
            if source.duration:
                minutes, seconds = divmod(source.duration, 60)
                duration_str = f" ({int(minutes):02d}:{int(seconds):02d})"
            queue_text += f"`{i+1}.` **{source.title}**{duration_str}\n"
        
        if len(queue) > 10:
            queue_text += f"\n... e mais **{len(queue) - 10}** músicas"
        
        embed.add_field(name="📝 Próximas na Fila", value=queue_text, inline=False)
    
    loop_status = "✅ Ativado" if music_bot.get_loop_mode(guild_id) else "❌ Desativado"
    embed.set_footer(text=f"Total na fila: {len(queue)} | Loop: {loop_status}")
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