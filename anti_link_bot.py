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
    """Vérifie que l'URL est directe et valide pour un GIF."""
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
        # Envoie le GIF sous forme d'URL dans le chat sans afficher le lien brut
        embed = discord.Embed(
            title=f"{msg.author.name} a partagé un GIF !",
            description=f"Voici le GIF envoyé par {msg.author.name}:",
            color=discord.Color.blue()
        )
        embed.set_image(url=direct_url)  # Ajoute le GIF dans l'embed
        embed.set_footer(text=f"Envoyé par {msg.author.name}", icon_url=msg.author.avatar.url)  # Footer avec l'avatar de l'utilisateur
        
        try:
            await msg.channel.send(embed=embed)  # Envoie le message
        except discord.Forbidden:
            pass
    else:
        # Si ce n'est pas un lien vers un GIF, on ignore
        return

bot.run(TOKEN)



