import discord
import random
import asyncio
from src.config import bot, EMOJIS_JOKENPO, JOKENPO_TIMEOUT

@bot.command(name="dado", aliases=["dice"], help="Rola um dado de 1 até o número máximo especificado.")
async def dado(ctx, dmax: str):
    try:
        max_val = int(dmax)
        if max_val < 1:
            embed = discord.Embed(title="❌ Erro", description="O número máximo deve ser pelo menos 1.", color=discord.Color.red())
            await ctx.reply(embed=embed, mention_author=True)
        else:
            resultado = random.randint(1, max_val)
            embed = discord.Embed(title="🎲 Dado Rolado!", description=f"**{resultado}** (1-{max_val})", color=discord.Color.blue())
            await ctx.reply(embed=embed, mention_author=True)
    except ValueError:
        embed = discord.Embed(title="❌ Erro", description="Por favor, forneça um número válido.", color=discord.Color.red())
        await ctx.reply(embed=embed, mention_author=True)

@bot.command(name="jokenpo", aliases=["rps"], help="Joga pedra, papel e tesoura com o bot.")
async def jokenpo(ctx):
    embed = discord.Embed(title="🎮 Jokenpô!", description="Vamos jogar pedra, papel e tesoura?\nEscolha uma opção reagindo com um dos emojis abaixo:", color=discord.Color.purple())
    msg = await ctx.send(embed=embed)

    for emoji in EMOJIS_JOKENPO:
        await msg.add_reaction(emoji)

    emoji_to_num = {"🪨": 1, "📄": 2, "✂️": 3}
    botchoice = random.randint(1, 3)

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in EMOJIS_JOKENPO and reaction.message.id == msg.id

    try:
        reaction, user = await bot.wait_for("reaction_add", check=check, timeout=JOKENPO_TIMEOUT)
    except asyncio.TimeoutError:
        embed = discord.Embed(title="⏰ Tempo Esgotado", description="Você demorou muito para reagir!", color=discord.Color.red())
        await ctx.send(embed=embed)
        return

    userchoice = emoji_to_num[str(reaction.emoji)]
    bot_emoji = {1: "🪨", 2: "📄", 3: "✂️"}[botchoice]

    # Determina o resultado e cor
    if userchoice == botchoice:
        result = f"{user.mention} nós empatamos!"
        result_color = discord.Color.yellow()
        title = "🤝 Empate!"
    elif (userchoice - botchoice) % 3 == 1:
        result = f"Parabéns {user.mention} você venceu!"
        result_color = discord.Color.green()
        title = "🎉 Vitória!"
    else:
        result = f"HAHAHA {user.mention} você perdeu pra um robô!"
        result_color = discord.Color.red()
        title = "🤖 Derrota!"

    embed = discord.Embed(title=title, color=result_color)
    embed.add_field(name="Você escolheu:", value=f"{EMOJIS_JOKENPO[str(reaction.emoji)]} {str(reaction.emoji)}", inline=True)
    embed.add_field(name="Eu escolhi:", value=f"{EMOJIS_JOKENPO[bot_emoji]} {bot_emoji}", inline=True)
    embed.add_field(name="Resultado:", value=result, inline=False)
    await ctx.send(embed=embed)