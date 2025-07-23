import discord
import os
import aiohttp

TOKEN = os.getenv("DISCORD_TOKEN")
TENOR_API_KEY = os.getenv("TENOR_API_KEY")  # Ta clé Tenor ici

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.message_attachments = True  # Pour détecter les fichiers envoyés
bot = discord.Client(intents=intents)

async def get_gif_from_tenor(search_term: str) -> str | None:
    """Recherche un GIF sur Tenor via API et renvoie l'URL GIF."""
    url = f"https://tenor.googleapis.com/v2/search?q={search_term}&key={TENOR_API_KEY}&limit=1&media_filter=gif"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                return None
            data = await response.json()
            if "results" in data and len(data["results"]) > 0:
                return data["results"][0]["media_formats"]["gif"]["url"]
            return None

@bot.event
async def on_ready():
    print(f"Bot connecté : {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # On vérifie si message contient des fichiers joints (attachments)
    if message.attachments:
        for attachment in message.attachments:
            if attachment.filename.lower().endswith(".gif"):
                embed = discord.Embed(
                    title=f"{message.author.name} a partagé un GIF !",
                    description=f"Voici un GIF envoyé par {message.author.name}:",
                    color=discord.Color.blue()
                )
                embed.set_image(url=attachment.url)
                embed.set_footer(text=f"Envoyé par {message.author.name}", icon_url=message.author.display_avatar.url)
                try:
                    await message.channel.send(embed=embed)
                except discord.Forbidden:
                    pass
                return  # Stop après premier GIF trouvé

    # Si pas de GIF en attachment, on peut gérer un trigger pour rechercher un GIF Tenor
    # Par exemple si message commence par "!gif <mot>"
    if message.content.startswith("!gif "):
        search_term = message.content[5:]
        gif_url = await get_gif_from_tenor(search_term)
        if gif_url:
            embed = discord.Embed(
                title=f"{message.author.name} a demandé un GIF Tenor !",
                description=f"Résultat pour : {search_term}",
                color=discord.Color.purple()
            )
            embed.set_image(url=gif_url)
            embed.set_footer(text=f"Demandé par {message.author.name}", icon_url=message.author.display_avatar.url)
            try:
                await message.channel.send(embed=embed)
            except discord.Forbidden:
                pass
        else:
            await message.channel.send("Désolé, aucun GIF trouvé pour cette recherche.")

bot.run(TOKEN)

