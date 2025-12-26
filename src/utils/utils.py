import discord
import subprocess
import os
from gtts import gTTS
from src.config import FFMPEG_EXECUTABLE, TTS_FILES, PITCH_FACTOR, TTS_LANG

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