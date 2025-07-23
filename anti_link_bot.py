import discord
import os
import re
import aiohttp  # Pour envoyer des requêtes HTTP asynchrones à l'API Tenor

# Récupère la clé API Tenor depuis tes variables d'environnement
TENOR_API_KEY = os.getenv("TENOR_API_KEY")

# Assure-toi que la clé API est bien définie
if not TENOR_API_KEY:
    raise ValueError("La clé API Tenor est nécessaire pour récupérer des GIFs de Tenor.")

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = discord.Client(intents=intents)

# Expression régulière pour attraper les URLs
URL_RE = re.compile(r"https?://\S+")

# Fonction pour vérifier si l'URL est un GIF valide (se termine par .gif)
async def get_direct_gif(url: str) -> str | None:
    """Vérifie si l'URL est un GIF valide (se termine par .gif)."""
    if url.endswith(".gif"):
        return url
    return None

# Fonction pour récupérer un GIF depuis Tenor via une recherche
async def get_gif_from_tenor(search_term: str) -> str:
    """Utilise l'API Tenor pour récupérer un GIF basé sur un terme de recherche."""
    url = f"https://api.tenor.com/v1/search?q={search_term}&key={TENOR_API_KEY}&limit=1"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                return None
            data = await response.json()
            gif_url = data['results'][0]['media'][0]['gif']['url']
            return gif_url

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
        # Si le lien est une recherche Tenor
        search_term = url.split("/")[-1]
        tenor_gif = await get_gif_from_tenor(search_term)
        if tenor_gif:
            embed = discord.Embed(
                title=f"{msg.author.name} a partagé un GIF de Tenor !",
                description=f"Voici un GIF envoyé par {msg.author.name}:",
                color=discord.Color.blue()  # Choix de couleur pour l'embed
            )
            embed.set_image(url=tenor_gif)  # Ajoute le GIF Tenor à l'embed
            embed.set_footer(text=f"Envoyé par {msg.author.name}", icon_url=msg.author.avatar.url)  # Ajouter l'avatar de l'utilisateur
            
            try:
                await msg.channel.send(embed=embed)  # Envoie le message avec l'embed
            except discord.Forbidden:
                pass
        else:
            return

bot.run(TOKEN)
