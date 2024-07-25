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
async def on_message(ctx):
    await ctx.reply("Eu sou tingbot", mention_author=True)


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

bot.run(discord_api_key)
