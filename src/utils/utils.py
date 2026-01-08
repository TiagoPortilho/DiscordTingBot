import discord
import subprocess
import os
import glob
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
    parts = [part.strip() for part in texto_and_pitch.split("|")]
    segments = []
    i = 0
    while i < len(parts):
        text = parts[i]
        if text == "":
            i += 1
            continue
        if i + 1 < len(parts):
            pitch_str = parts[i + 1]
            try:
                pitch = float(pitch_str) if pitch_str else PITCH_FACTOR
            except ValueError:
                raise ValueError(f"Pitch inválido: '{pitch_str}'. Use um número.")
            segments.append((text, pitch))
            i += 2
        else:
            segments.append((text, PITCH_FACTOR))
            i += 1
    if not segments:
        raise ValueError("Nenhum texto fornecido.")
    return segments

# Função auxiliar para gerar e processar TTS
def generate_tts_audio(segments):
    audio_files = []
    for i, (texto, pitch) in enumerate(segments):
        tts = gTTS(texto, lang=TTS_LANG)
        temp_file = f'tts_segment_{i}.mp3'
        tts.save(temp_file)
        if pitch != 1.0:
            try:
                pitched_file = f'tts_segment_{i}_pitched.mp3'
                subprocess.run([
                    FFMPEG_EXECUTABLE, '-y', '-i', temp_file,
                    '-filter:a', f'asetrate=44100*{pitch},aresample=44100,atempo=1.0', pitched_file
                ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                audio_files.append(pitched_file)
                os.remove(temp_file)
            except Exception as e:
                print(f'FFmpeg pitch shift failed for segment {i}: {e} — using original')
                audio_files.append(temp_file)
        else:
            audio_files.append(temp_file)
    
    if len(audio_files) == 1:
        return audio_files[0]
    
    # Concatenate multiple files
    concat_file = 'tts_output.mp3'
    with open('file_list.txt', 'w') as f:
        for file in audio_files:
            f.write(f"file '{file}'\n")
    try:
        subprocess.run([
            FFMPEG_EXECUTABLE, '-y', '-f', 'concat', '-safe', '0', '-i', 'file_list.txt', '-c', 'copy', concat_file
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f'FFmpeg concat failed: {e} — using first file')
        concat_file = audio_files[0]
    
    # Cleanup segment files
    for file in audio_files:
        try:
            if os.path.exists(file):
                os.remove(file)
        except Exception:
            pass
    if os.path.exists('file_list.txt'):
        os.remove('file_list.txt')
    
    return concat_file

# Função auxiliar para limpar arquivos TTS
def cleanup_tts_files():
    import glob
    for pattern in ['tts_*.mp3', 'file_list.txt']:
        for f in glob.glob(pattern):
            try:
                os.remove(f)
            except Exception:
                pass
    print('Arquivos TTS removidos.')