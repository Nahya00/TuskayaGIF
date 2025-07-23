import discord
import os
import re

TOKEN     = os.getenv("DISCORD_TOKEN")
GIF_SITES = ("tenor.com", "media.tenor.com", "giphy.com", "media.giphy.com")

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = discord.Client(intents=intents)

URL_RE = re.compile(r"https?://\S+")

async def get_direct_gif(url: str) -> str | None:
    """Vérifie si l'URL est un GIF valide (se termine par .gif)."""
    if url.endswith(".gif"):
        return url
    return None

@bot.event
async def on_ready():
    print(f"Bot connecté : {bot.user}")

@bot.event
async def on_message(msg):
    if msg.author.bot:
        return

    # Recherche des liens dans le message
    m = URL_RE.search(msg.content)
    if not m:
        return

    url = m.group(0)
    direct_url = await get_direct_gif(url)

    if direct_url:
        # Envoyer directement le GIF avec le nom de l'utilisateur
        try:
            await msg.channel.send(f"{msg.author.name} a partagé un GIF :", file=discord.File(direct_url))
        except discord.Forbidden:
            pass
    else:
        return

bot.run(TOKEN)




