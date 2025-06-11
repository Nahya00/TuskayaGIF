import discord
import os
import re

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = discord.Client(intents=intents)

URL_RE = re.compile(r"https?://\S+")
WHITELIST = ("tenor.com", "giphy.com", "media.tenor.com", "media.giphy.com")

@bot.event
async def on_ready():
    print(f"Connecté : {bot.user}")

@bot.event
async def on_message(msg):
    if msg.author.bot:
        return

    match = URL_RE.search(msg.content)
    if not match:
        return

    url = match.group(0)
    domain = url.split("/")[2]

    # ----- GIF autorisé -----
    if domain.endswith(WHITELIST):
        try:
            await msg.delete()
        except discord.Forbidden:
            pass

        embed = discord.Embed(color=discord.Color.dark_blue())  # <- plus de description
        embed.set_author(name=str(msg.author), icon_url=msg.author.display_avatar.url)
        embed.set_image(url=url)

        await msg.channel.send(embed=embed)

    # ----- Lien interdit -----
    else:
        try:
            await msg.delete()
        except discord.Forbidden:
            pass
        warn = discord.Embed(description="**Lien interdit supprimé.**",
                             color=discord.Color.red())
        warn.set_author(name=str(msg.author), icon_url=msg.author.display_avatar.url)
        await msg.channel.send(embed=warn, delete_after=5)

bot.run(os.getenv("DISCORD_TOKEN"))

