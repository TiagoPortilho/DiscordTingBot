import discord
from src.config import bot, DISCORD_API_KEY
from discord.ext import commands

# Importar todos os comandos dos módulos
import src.commands.game_commands
import src.commands.tts_commands  
import src.commands.music_commands

bot.help_command = None

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

@bot.command(name="ping", help="Verifica a latência do bot.")
async def ping(ctx):
    embed = discord.Embed(title="🏓 Pong!", description=f"Latência: **{round(bot.latency * 1000)}ms**", color=discord.Color.green())
    await ctx.reply(embed=embed, mention_author=True)

@bot.command(name="sair", aliases=["exit"], help="Faz o bot sair do canal de voz.")
async def sair(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        embed = discord.Embed(title="👋 Tchau!", description="Saí do canal de voz!", color=discord.Color.orange())
        await ctx.reply(embed=embed, mention_author=True)
    else:
        embed = discord.Embed(title="❌ Erro", description="Não estou em nenhum canal de voz.", color=discord.Color.red())
        await ctx.reply(embed=embed, mention_author=True)

@bot.command(name="help", aliases=["ajuda"], help="Mostra todos os comandos disponíveis.")
async def help_command(ctx):
    embed = discord.Embed(
        title="TingBot - Ajuda",
        description="**Bem-vindo ao TingBot!**\n*Todos os comandos usam o prefixo `$` *",
        color=discord.Color.from_rgb(88, 101, 242)  # Discord Blurple
    )
    
    embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/749750394142523402.png")  # Bot emoji

    # Comandos Básicos
    embed.add_field(
        name="**Comandos Básicos**",
        value="`$ping` - Verifica latência do bot\n"
              "`$sair` / `$exit` - Remove o bot do canal de voz",
        inline=True
    )

    # Diversão & Jogos
    embed.add_field(
        name="**Jogos & Diversão**",
        value="`$dado` / `$dice <número>` - Rola um dado\n"
              "`$jokenpo` / `$rps` - Pedra, papel e tesoura",
        inline=True
    )

    # TTS
    embed.add_field(
        name="**Text-to-Speech**",
        value="`$falar` / `$speak <texto>` - Bot fala seu texto\n"
              "`$tts_fila` / `$tf` - Ver fila de mensagens TTS",
        inline=True
    )

    # Controles de Música
    embed.add_field(
        name="**Player de Música**",
        value="`$tocar` / `$play <música>` - Tocar música\n"
              "`$pausar` / `$pause` - Pausar música\n"
              "`$continuar` / `$resume` - Retomar música\n"
              "`$parar` / `$stop` - Parar e limpar fila",
        inline=False
    )

    # Gerenciamento de Fila
    embed.add_field(
        name="**Fila & Controles**",
        value="`$pular` / `$skip` - Próxima música\n"
              "`$fila` / `$queue` - Ver fila de músicas\n"
              "`$loop` / `$repetir` - Ativar/desativar loop",
        inline=True
    )

    # Configurações de Áudio  
    embed.add_field(
        name="**Configurações**",
        value="`$volume` / `$vol <0-100>` - Ajustar volume\n"
              "`$tocando` / `$np` - Info da música atual",
        inline=True
    )

    # Dicas especiais
    embed.add_field(
        name="**Dicas Especiais**",
        value="• **TTS com Pitch**: Use `$falar texto | 0.8` para voz mais grave\n"
              "• **URLs do YouTube**: Cole links diretos para tocar\n"
              "• **TTS + Música**: TTS entra na fila se música estiver tocando",
        inline=False
    )

    embed.set_footer(
        text="Desenvolvido por https://github.com/TiagoPortilho",
        icon_url="https://github.githubassets.com/favicons/favicon.png"
    )
    
    await ctx.send(embed=embed)

if __name__ == "__main__":
    bot.run(DISCORD_API_KEY)