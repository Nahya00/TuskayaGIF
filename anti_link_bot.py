import discord, os, re, aiohttp, mimetypes
from io import BytesIO

TOKEN      = os.getenv("DISCORD_TOKEN")
TENOR_KEY  = os.getenv("TENOR_KEY")      # optionnel mais recommandé
MAX_SIZE   = 25 * 1024 * 1024             # passe à 25 * 1024 * 1024 si Nitro

bot = discord.Client(intents=discord.Intents.all())
URL_RE = re.compile(r"https?://\S+")
ALLOWED = ("tenor.com", "giphy.com", "media.tenor.com", "media.giphy.com")

# ───────────────────────── helpers ──────────────────────────
async def tenor_api(url: str) -> str | None:
    """Retourne le lien GIF via l’API officielle (si TENOR_KEY dispo)."""
    if not TENOR_KEY:                     # pas de clé ➜ on saute
        return None
    gif_id = url.rstrip("/").split("-")[-1]
    api = (f"https://tenor.googleapis.com/v2/posts"
           f"?ids={gif_id}&key={TENOR_KEY}&media_filter=gif")
    async with aiohttp.ClientSession() as s:
        try:
            async with s.get(api, timeout=8) as r:
                if r.status != 200:
                    return None
                data = await r.json()
        except Exception:                 # réseau down ↘
            return None
    return (
        data.get("results", [{}])[0]
            .get("media_formats", {})
            .get("gif", {})
            .get("url")
    )

def to_cdn(url: str) -> str:
    """Construit un lien CDN ‘.gif’ simple pour Tenor/Giphy."""
    if "tenor.com" in url and url.split("-")[-1].isdigit():
        gif_id = url.rstrip("/").split("-")[-1]
        return f"https://media.tenor.com/{gif_id}/tenor.gif"
    if "giphy.com" in url:
        gif_id = url.rstrip("/").split("-")[-1]
        return f"https://media.giphy.com/media/{gif_id}/giphy.gif"
    return url

async def fetch(url: str):
    """Télécharge si content-type image/gif + ≤ MAX_SIZE."""
    async with aiohttp.ClientSession() as s:
        try:
            async with s.get(url, timeout=10) as r:
                if r.status != 200:
                    return None, None
                ct = r.headers.get("content-type", "")
                if not ct.startswith(("image/", "video/")):  # évite HTML
                    return None, None
                data = await r.read()
                if len(data) > MAX_SIZE:
                    return None, None
                ext = mimetypes.guess_extension(ct.split(";")[0]) or ".gif"
                return data, ext.lstrip(".")
        except Exception:
            return None, None

# ───────────────────────── events ───────────────────────────
@bot.event
async def on_message(m):
    if m.author.bot:
        return

    match = URL_RE.search(m.content)
    if not match:
        return
    url = match.group(0)
    if not any(url.split("/")[2].endswith(d) for d in ALLOWED):
        return

    # 1️⃣ essaie API Tenor (fiable)
    direct = await tenor_api(url) or to_cdn(url)

    # 2️⃣ télécharge
    data, ext = await fetch(direct)
    await m.delete()

    embed = discord.Embed(description="\u200b", color=discord.Color.dark_blue())
    embed.set_author(name=str(m.author), icon_url=m.author.display_avatar.url)

    files = None
    if data:
        fname = f"gif.{ext}"
        files = [discord.File(BytesIO(data), filename=fname)]
        embed.set_image(url=f"attachment://{fname}")
    else:                      # encore un raté ➜ lien direct (meilleur effort)
        embed.set_image(url=direct)

    await m.channel.send(embed=embed, files=files)

bot.run(TOKEN)

