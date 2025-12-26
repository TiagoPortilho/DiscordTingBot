import discord
from src.config import bot, FFMPEG_EXECUTABLE
from src.utils.utils import connect_to_voice, parse_texto_and_pitch, generate_tts_audio, cleanup_tts_files

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