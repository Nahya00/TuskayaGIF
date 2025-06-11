
import discord, os, re, aiohttp
from io import BytesIO

# ----- Configuration -----
DOMAINS = ("tenor.com", "media.tenor.com", "giphy.com", "media.giphy.com")
MAX_SIZE = 25 * 1024 * 1024  # 8 Mo

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = discord.Client(intents=intents)

URL_RE = re.compile(r"https?://\S+")

# -------------------------------------------------
# Helpers
# -------------------------------------------------
async def fetch_bytes(url: str):
    """Télécharge le contenu du fichier (<= MAX_SIZE)"""
    async with aiohttp.ClientSession() as s:
        try:
            async with s.get(url, timeout=10) as r:
                if r.status != 200:
                    return None, None
                data = await r.read()
                if len(data) > MAX_SIZE:
                    return None, None
                ct = r.headers.get("content-type", "")
                ext = ct.split("/")[-1].split(";")[0] or "gif"
                return data, ext
        except Exception:
            return None, None

def tenor_cdn(url: str):
    """Convertit une URL tenor.com/... en media.tenor.com/<ID>/tenor.gif"""
    gif_id = url.rstrip("/").split("-")[-1]
    if gif_id.isdigit():
        return f"https://media.tenor.com/{gif_id}/tenor.gif"
    return url

def giphy_cdn(url: str):
    """Convertit giphy.com/... en media.giphy.com/media/<ID>/giphy.gif"""
    parts = url.rstrip("/").split("-")
    gif_id = parts[-1]
    # ID giphy est souvent mélange de lettres/chiffres >= 5 car
    if gif_id:
        return f"https://media.giphy.com/media/{gif_id}/giphy.gif"
    return url

def to_cdn(url: str):
    if "tenor.com" in url:
        return tenor_cdn(url)
    if "giphy.com" in url:
        return giphy_cdn(url)
    return url

# -------------------------------------------------
# Events
# -------------------------------------------------
@bot.event
async def on_ready():
    print("Connecté :", bot.user)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    match = URL_RE.search(message.content)
    if not match:
        return

    link = match.group(0)
    if not any(link.split("/")[2].endswith(d) for d in DOMAINS):
        return  # lien pas concerné

    cdn_url = to_cdn(link)
    data, ext = await fetch_bytes(cdn_url)

    try:
        await message.delete()
    except discord.Forbidden:
        pass

    embed = discord.Embed(description="\u200b", color=discord.Color.dark_blue())
    embed.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)

    files = None
    if data:
        fname = f"gif.{ext}"
        file_obj = discord.File(BytesIO(data), filename=fname)
        embed.set_image(url=f"attachment://{fname}")
        files = [file_obj]
    else:
        embed.set_image(url=cdn_url)

    await message.channel.send(embed=embed, files=files)

if __name__ == "__main__":
    bot.run(os.getenv("DISCORD_TOKEN"))
