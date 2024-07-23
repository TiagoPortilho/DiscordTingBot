import discord
import random
import os
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

discord_api_key = os.getenv("DISCORD_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

class Tingbot(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        if message.author.id == self.user.id:
            return

        if message.content.startswith("$ola"):
            await message.reply("Eu sou tingbot", mention_author=True)

        if message.content.startswith("$dado"):
            parts = message.content.split()
            dmax = int(parts[1])
            await message.reply(random.randint(1, dmax), mention_author=True)

        if message.content.startswith("$t"):
            sexo = message.content[3:]
            await message.reply(sexo)


intents = discord.Intents.default()
intents.message_content = True

client = Tingbot(intents=intents)
client.run(discord_api_key)
