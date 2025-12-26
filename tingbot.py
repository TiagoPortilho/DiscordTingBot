import discord
from src.config import bot, DISCORD_API_KEY
from discord.ext import commands

# Importar todos os comandos dos módulos
import src.commands.game_commands
import src.commands.tts_commands  
import src.commands.music_commands

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

if __name__ == "__main__":
    bot.run(DISCORD_API_KEY)