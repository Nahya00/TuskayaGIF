import discord, os, re, aiohttp

TOKEN     = os.getenv("DISCORD_TOKEN")
TENOR_KEY = os.getenv("TENOR_KEY")          # clé Tenor v2
GIF_SITES = ("tenor.com", "media.tenor.com",
             "giphy.com", "media.giphy.com")

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = discord.Client(intents=intents)

URL_RE = re.compile(r"https?://\S+")

async def tenor_gif(url: str) -> str | None:
    """Renvoie le .gif direct avec la clé Tenor (ou None)."""
    if not TENOR_KEY or "tenor.com" not in url:
        return None

    gif_id = url.rstrip("/").split("-")[-1]
    if not gif_id.isdigit():
        return None

    api = (f"https://tenor.googleapis.com/v2/posts"
           f"?ids={gif_id}&key={TENOR_KEY}&media_filter=gif")

    async with aiohttp.ClientSession() as s:
        try:
            async with s.get(api, timeout=8) as r:
                if r.status != 200:
                    return None
                data = await r.json()
        except Exception as e:
            print(f"[Tenor API] Erreur : {e}")
            return None

    return (
        data.get("results", [{}])[0]
            .get("media_formats", {})
            .get("gif", {})
            .get("url")
    )

async def giphy_gif(url: str) -> str | None:
    """Retourne l'URL du GIF direct depuis Giphy (ou None)."""
    if "giphy.com" not in url:
        return None

    gif_id = url.rstrip("/").split("-")[-1]
    api = f"https://api.giphy.com/v1/gifs/{gif_id}?api_key={os.getenv('GIPHY_API_KEY')}"
    
    async with aiohttp.ClientSession() as s:
        try:
            async with s.get(api, timeout=8) as r:
                if r.status != 200:
                    return None
                data = await r.json()
        except Exception as e:
            print(f"[Giphy API] Erreur : {e}")
            return None

    return data.get("data", {}).get("images", {}).get("original", {}).get("url")

@bot.event
async def on_ready():
    print("Connecté :", bot.user)

@bot.event
async def on_message(msg):
    if msg.author.bot:
        return

    m = URL_RE.search(msg.content)
    if not m:
        return

    url = m.group(0)
    if not any(url.split("/")[2].endswith(d) for d in GIF_SITES):
        return

    # Tentative de récupération de GIF direct (Tenor ou Giphy)
    direct = await tenor_gif(url) if "tenor.com" in url else await giphy_gif(url) if "giphy.com" in url else url
    direct = direct or url

    # Supprimer le message original (optionnel)
    try:
        await msg.delete()
    except discord.Forbidden:
        pass

    # Réenvoi simple du lien direct
    try:
        await msg.channel.send(f"{direct}")
    except discord.Forbidden:
        pass

bot.run(TOKEN)

