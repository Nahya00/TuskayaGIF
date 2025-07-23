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

async def get_direct_gif(url: str) -> bool:
    """Vérifie si l'URL est directe et valide pour un GIF."""
    if url.endswith(".gif"):
        return True
    return False

@bot.event
async def on_ready():
    print(f"Bot connecté : {bot.user}")

@bot.event
async def on_message(msg):
    if msg.author.bot:
        return

    # Recherche des URL dans le message
    m = URL_RE.search(msg.content)
    if not m:
        return

    url = m.group(0)
    if await get_direct_gif(url):
        # Si c'est un lien vers un GIF, Discord l'affichera automatiquement
        try:
            await msg.channel.send(f"{msg.author.name} a envoyé un GIF : {url}")
        except discord.Forbidden:
            pass

bot.run(TOKEN)


