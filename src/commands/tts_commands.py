import discord
import asyncio
from collections import deque
from src.config import bot, FFMPEG_EXECUTABLE
from src.utils.utils import connect_to_voice, parse_texto_and_pitch, generate_tts_audio, cleanup_tts_files
from src.commands.music_commands import music_bot

class TTSBot:
    def __init__(self, bot):
        self.bot = bot
        self.tts_queues = {}  # Fila de TTS por servidor
        self.tts_playing = {}  # Status de TTS tocando por servidor

    def get_tts_queue(self, guild_id):
        if guild_id not in self.tts_queues:
            self.tts_queues[guild_id] = deque()
        return self.tts_queues[guild_id]

    def is_tts_playing(self, guild_id):
        return self.tts_playing.get(guild_id, False)

    def set_tts_playing(self, guild_id, playing):
        self.tts_playing[guild_id] = playing

    async def play_tts_after_music(self, ctx, tts_data):
        """Toca TTS após a música terminar"""
        guild_id = ctx.guild.id
        vc = ctx.voice_client

        if not vc:
            return

        # Marca que TTS está tocando
        self.set_tts_playing(guild_id, True)

        def after_tts(error):
            if error:
                print(f"Erro no TTS: {error}")
            cleanup_tts_files()
            self.set_tts_playing(guild_id, False)

            # Verifica se há mais TTS na fila
            queue = self.get_tts_queue(guild_id)
            if queue:
                # Agenda o próximo TTS
                next_tts = queue.popleft()
                asyncio.run_coroutine_threadsafe(
                    self.play_tts_after_music(ctx, next_tts), bot.loop
                )

        vc.play(discord.FFmpegPCMAudio(tts_data['file'], executable=FFMPEG_EXECUTABLE), after=after_tts)

        # Enviar confirmação
        embed = discord.Embed(
            title="🗣️ TTS na Fila",
            description=f"Falando após música: **{tts_data['texto'][:100]}{'...' if len(tts_data['texto']) > 100 else ''}**",
            color=discord.Color.blue()
        )
        if tts_data['pitch'] != 1.0:
            embed.add_field(name="Pitch", value=f"{tts_data['pitch']}x", inline=True)
        await ctx.send(embed=embed)

tts_bot = TTSBot(bot)

@bot.command(name='falar', aliases=['speak'], help="Fala o texto fornecido em um canal de voz usando TTS. Opcional: | <pitch> para ajustar profundidade da voz (ex: 0.8 para mais grave; padrão usa 0.85).")
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
    guild_id = ctx.guild.id

    # Verifica se há música tocando
    current_music = music_bot.get_current(guild_id)

    if current_music and (vc.is_playing() or vc.is_paused()):
        # Há música tocando - adiciona TTS à fila
        tts_data = {
            'file': play_file,
            'texto': texto,
            'pitch': pitch
        }

        queue = tts_bot.get_tts_queue(guild_id)
        queue.append(tts_data)

        embed = discord.Embed(
            title="📝 TTS Adicionado à Fila",
            description=f"**{texto[:100]}{'...' if len(texto) > 100 else ''}**",
            color=discord.Color.orange()
        )
        embed.add_field(name="Posição na fila", value=f"#{len(queue)}", inline=True)
        if pitch != 1.0:
            embed.add_field(name="Pitch", value=f"{pitch}x", inline=True)
        await ctx.send(embed=embed)

    else:
        # Não há música tocando - toca TTS imediatamente
        def after_playing(error):
            if error:
                print(f"Erro ao reproduzir o áudio: {error}")
            cleanup_tts_files()
            tts_bot.set_tts_playing(guild_id, False)

        tts_bot.set_tts_playing(guild_id, True)
        vc.play(discord.FFmpegPCMAudio(play_file, executable=FFMPEG_EXECUTABLE), after=after_playing)

        # Enviar confirmação com embed
        embed = discord.Embed(title="🗣️ TTS Ativo", description=f"Falando: **{texto[:100]}{'...' if len(texto) > 100 else ''}**", color=discord.Color.blue())
        if pitch != 1.0:
            embed.add_field(name="Pitch", value=f"{pitch}x", inline=True)
        await ctx.send(embed=embed)

@bot.command(name='tts_fila', aliases=['tts_queue', 'tf'], help='Mostra a fila de mensagens TTS')
async def tts_fila(ctx):
    guild_id = ctx.guild.id
    queue = tts_bot.get_tts_queue(guild_id)

    if not queue:
        embed = discord.Embed(title="📝 Fila TTS Vazia", description="Não há mensagens TTS na fila.", color=discord.Color.orange())
        await ctx.send(embed=embed)
        return

    embed = discord.Embed(title="🗣️ Fila de TTS", color=discord.Color.purple())

    queue_text = ""
    for i, tts_item in enumerate(list(queue)[:10]):  # Mostra até 10 mensagens
        texto_preview = tts_item['texto'][:80] + "..." if len(tts_item['texto']) > 80 else tts_item['texto']
        pitch_info = f" ({tts_item['pitch']}x)" if tts_item['pitch'] != 1.0 else ""
        queue_text += f"`{i+1}.` **{texto_preview}**{pitch_info}\n"

    if len(queue) > 10:
        queue_text += f"\n... e mais **{len(queue) - 10}** mensagens"

    embed.add_field(name="📝 Próximas Mensagens", value=queue_text, inline=False)
    embed.set_footer(text=f"Total na fila: {len(queue)}")
    await ctx.send(embed=embed)