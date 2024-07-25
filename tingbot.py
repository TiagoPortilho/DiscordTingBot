import discord
import random
import os
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()

discord_api_key = os.getenv("DISCORD_API_KEY")

description = " "

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='$', description=description, intents=intents)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')


@bot.command(name="ola")
async def ola(ctx):
    await ctx.reply("Olá, eu sou tingbot", mention_author=True)


@bot.command(name="dado")
async def dado(ctx, dmax: int):
    await ctx.reply(random.randint(1, dmax), mention_author=True)


@bot.command(name="jokenpo")
async def jokenpo(ctx):
    await ctx.send("Vamos jogar pedra, papel e tesoura?\n"
                   "1 - Pedra\n"
                   "2 - Papel\n"
                   "3 - Tesoura\n"
                   "Digite um número:\n")

    list_jokenpo = {1: "Pedra", 2: "Papel", 3: "Tesoura"}
    botchoice = random.randint(1, 3)

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        msg = await bot.wait_for("message", check=check, timeout=30)
    except TimeoutError:
        await ctx.send("Você demorou muito para responder!")
    else:
        userchoice = int(msg.content)
        if (userchoice == 1 and botchoice == 3) or (userchoice == 2 and botchoice == 1) or (userchoice == 3 and
                                                                                            botchoice == 2):
            await ctx.send("Você escolheu: " + str(list_jokenpo[userchoice]) + "\nEu escolhi: "
                           + str(list_jokenpo[botchoice]))
            await ctx.send(f"Parabéns {msg.author.mention} você venceu!")

        elif (userchoice == 3 and botchoice == 1) or (userchoice == 1 and botchoice == 2) or (userchoice == 2 and
                                                                                              botchoice == 3):
            await ctx.send("Você escolheu: " + str(list_jokenpo[userchoice]) + "\nEu escolhi: "
                           + str(list_jokenpo[botchoice]))
            await ctx.send(f"HAHAHA {msg.author.mention} você perdeu pra um robô!")

        elif (userchoice == 1 and botchoice == 1) or (userchoice == 2 and botchoice == 2) or (userchoice == 3 and
                                                                                              botchoice == 3):
            await ctx.send("Você escolheu: " + str(list_jokenpo[userchoice]) + "\nEu escolhi: "
                           + str(list_jokenpo[botchoice]))
            await ctx.send(f"{msg.author.mention} nós empatamos!")

        else:
            await ctx.send("Selecione uma opção válida.")


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

    class MyHelp(commands.HelpCommand):
        async def send_error_message(self, error):
            embed = discord.Embed(title="Error", description=error, color=discord.Color.red())
            channel = self.get_destination()

            await channel.send(embed=embed)


bot.help_command = MyHelp()

bot.run(discord_api_key)
