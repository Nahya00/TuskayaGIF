
import discord, os, re, aiohttp, mimetypes
from io import BytesIO

# Tokens clés via variables d'environnement
TOKEN      = os.getenv("DISCORD_TOKEN")
TENOR_KEY  = os.getenv("TENOR_KEY")      # facultatif mais recommandé

# Configuration
MAX_BYTES  = 8 * 1024 * 1024             # 8 Mo (augmente si Nitro / Boost)
DOMAINS    = ("tenor.com", "media.tenor.com",
              "giphy.com", "media.giphy.com")

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True          # activer dans le portail Discord
bot = discord.Client(intents=intents)

URL_RE = re.compile(r"https?://\S+")

# ── Tenor API pour lien .gif direct ────────────────────────────────
async def tenor_api_gif(url: str) -> str | None:
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
        except Exception:
            return None
    return (
        data.get("results", [{}])[0]
            .get("media_formats", {})
            .get("gif", {})
            .get("url")
    )

# ── Téléchargement (GIF ou MP4) ───────────────────────────────────
async def fetch_file(url: str):
    async with aiohttp.ClientSession() as s:
        try:
            async with s.get(url, timeout=10) as r:
                if r.status != 200:
                    return None, None
                data = await r.read()
                if len(data) > MAX_BYTES:
                    return None, None
                ctype = r.headers.get("content-type", "").split(";")[0]
                if not (ctype.startswith("image/") or ctype == "video/mp4"):
                    return None, None
                ext = mimetypes.guess_extension(ctype) or ".gif"
                return data, ext.lstrip(".")
        except Exception:
            return None, None

# ── Extraction du lien dans message ou embeds ────────────────────
def extract_link(msg: discord.Message) -> str | None:
    m = URL_RE.search(msg.content)
    if m and any(m.group(0).split('/')[2].endswith(d) for d in DOMAINS):
        return m.group(0)
    for emb in msg.embeds:
        if emb.url and any(emb.url.split('/')[2].endswith(d) for d in DOMAINS):
            return emb.url
        if emb.thumbnail and emb.thumbnail.url:
            thumb = emb.thumbnail.url
            if any(thumb.split('/')[2].endswith(d) for d in DOMAINS):
                return thumb
    return None

# ── Events ───────────────────────────────────────────────────────
@bot.event
async def on_ready():
    print("Bot connecté :", bot.user)

@bot.event
async def on_message(msg: discord.Message):
    if msg.author.bot:
        return

    url = extract_link(msg)
    if not url:
        return

    # ⇢ Option Tenor API pour un .gif fiable
    if "tenor.com" in url:
        api_url = await tenor_api_gif(url)
        if api_url:
            url = api_url

    # Supprime le message original
    try:
        await msg.delete()
    except discord.Forbidden:
        return  # pas de permission, on abandonne

    # Télécharge (si <= MAX_BYTES) sinon fallback
    data, ext = await fetch_file(url)

    embed = discord.Embed(description="\u200b", color=discord.Color.dark_blue())
    embed.set_author(name=str(msg.author), icon_url=msg.author.display_avatar.url)

    files = None
    if data:
        fname = f"gif.{ext}"
        files = [discord.File(BytesIO(data), filename=fname)]
        embed.set_image(url=f"attachment://{fname}")
    else:
        embed.set_image(url=url)

    await msg.channel.send(embed=embed, files=files)

if __name__ == "__main__":
    bot.run(TOKEN)


