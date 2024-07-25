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


bot.run(discord_api_key)
