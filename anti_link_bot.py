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

    # Recherche des URL dans le message
    m = URL_RE.search(msg.content)
    if not m:
        return

    url = m.group(0)
    direct_url = await get_direct_gif(url)

    if direct_url:
        # Crée un embed avec le GIF et mentionne uniquement le nom de l'utilisateur
        embed = discord.Embed(
            title=f"{msg.author.name} a partagé un GIF !",
            description=f"Voici le GIF envoyé par {msg.author.name}:",
            color=discord.Color.blue()  # Choix de couleur pour l'embed
        )
        embed.set_image(url=direct_url)  # Ajoute le GIF à l'embed
        embed.set_footer(text=f"Envoyé par {msg.author.name}", icon_url=msg.author.avatar.url)  # Ajouter l'avatar de l'utilisateur
        
        # Envoie de l'embed dans le salon
        try:
            await msg.channel.send(embed=embed)  # Envoie le message avec l'embed
        except discord.Forbidden:
            pass
    else:
        return

bot.run(TOKEN)


