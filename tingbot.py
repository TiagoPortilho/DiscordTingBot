import discord
import random

discord_api_key = "MTI2NDk2NDQyOTE1NDQ4NDMwNw.GmsHP3.yKZx1wk_0edZ_Ptb6TVjKbAoVx8UycGRnhHWoQ"


class MyClient(discord.Client):
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


intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run(discord_api_key)
