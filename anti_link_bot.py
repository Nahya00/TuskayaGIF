# bot.py
import os, re, mimetypes, aiohttp, discord
from io import BytesIO
from dotenv import load_dotenv

# ───── Chargement des clés ──────────────────────────────────────────
load_dotenv()  
TOKEN     = os.getenv("DISCORD_TOKEN")
TENOR_KEY = os.getenv("TENOR_KEY")   # ta clé Tenor v2, sinon None

# ───── Configuration Discord ────────────────────────────────────────
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True       # active aussi dans le Dev Portal !
bot = discord.Client(intents=intents)

# ───── Constantes ──────────────────────────────────────────────────
URL_RE   = re.compile(r"https?://\S+")
DOMAINS  = ("tenor.com", "media.tenor.com",
            "giphy.com", "media.giphy.com")
MAX_SIZE = 8 * 1024 * 1024           # 8 Mo max (monte à 25 Mo si Nitro)

# ───── Helper : Obtenir l’URL .gif via l’API Tenor ────────────────
async def fetch_tenor_gif(url: str) -> str | None:
    if not TENOR_KEY or "tenor.com" not in url:
        return None
    gif_id = url.rstrip("/").split("-")[-1]
    if not gif_id.isdigit():
        return None
    api = (
        f"https://tenor.googleapis.com/v2/posts"
        f"?ids={gif_id}&key={TENOR_KEY}&media_filter=gif"
    )
    async with aiohttp.ClientSession() as s:
        try:
            async with s.get(api, timeout=8) as r:
                if r.status != 200:
                    return None
                data = await r.json()
        except Exception:
            return None
    return (
        data.get("results", [{}])[0]
            .get("media_formats", {})
            .get("gif", {})
            .get("url")
    )

# ───── Helper : Téléchargement + détection de l’extension ─────────
async def fetch_media(url: str):
    async with aiohttp.ClientSession() as s:
        try:
            async with s.get(url, timeout=10) as r:
                if r.status != 200:
                    return None, None
                ctype = r.headers.get("content-type", "").split(";")[0]
                if not (ctype.startswith("image/") or ctype == "video/mp4"):
                    return None, None
                data = await r.read()
                if len(data) > MAX_SIZE:
                    return None, None
                ext = mimetypes.guess_extension(ctype) or ".gif"
                return data, ext.lstrip(".")
        except Exception:
            return None, None

# ───── Helper : Extraction d’un lien Tenor/Giphy ───────────────────
def extract_link(msg: discord.Message) -> str | None:
    # 1) dans le contenu texte
    m = URL_RE.search(msg.content or "")
    if m and any(m.group(0).split("/")[2].endswith(d) for d in DOMAINS):
        return m.group(0)
    # 2) dans les embeds (Favoris / stamp)
    for emb in msg.embeds:
        u = getattr(emb, "url", None)
        if u and any(u.split("/")[2].endswith(d) for d in DOMAINS):
            return u
        thumb = getattr(emb.thumbnail, "url", None)
        if thumb and any(thumb.split("/")[2].endswith(d) for d in DOMAINS):
            return thumb
    return None

# ───── Événements Discord ───────────────────────────────────────────
@bot.event
async def on_ready():
    print("Connecté en tant que", bot.user)

@bot.event
async def on_message(msg: discord.Message):
    if msg.author.bot:
        return

    url = extract_link(msg)
    if not url:
        return

    # 1) si Tenor, essaie l’API pour un .gif direct
    direct = await fetch_tenor_gif(url) if "tenor.com" in url else None
    direct = direct or url

    # 2) télécharge le média (≤ MAX_SIZE)
    data, ext = await fetch_media(direct)

    # 3) construit l’embed
    embed = discord.Embed(description="\u200b",
                          color=discord.Color.dark_blue())
    embed.set_author(name=str(msg.author),
                     icon_url=msg.author.display_avatar.url)

    files = None
    if data:
        fname = f"media.{ext}"
        files = [discord.File(BytesIO(data), filename=fname)]
        embed.set_image(url=f"attachment://{fname}")
    else:
        embed.set_image(url=direct)

    # 4) envoie l’embed **avant** de supprimer
    await msg.channel.send(embed=embed, files=files)

    # 5) supprime le message d’origine
    try:
        await msg.delete()
    except discord.Forbidden:
        pass

# ───── Lancement du bot ─────────────────────────────────────────────
bot.run(TOKEN)


