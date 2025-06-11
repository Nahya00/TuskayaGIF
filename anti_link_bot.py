import discord, os, re, aiohttp
from io import BytesIO

bot = discord.Client(intents=discord.Intents.all())

URL_RE   = re.compile(r"https?://\S+")
DOMAINS  = ("tenor.com", "giphy.com", "media.tenor.com", "media.giphy.com")
MAX_SIZE = 8 * 1024 * 1024                         # 8 Mo

async def download(url: str):
    async with aiohttp.ClientSession() as s:
        async with s.get(url, timeout=10) as r:
            if r.status != 200:
                return None, None
            data = await r.read()
            if len(data) > MAX_SIZE:
                return None, None
            ext = r.headers.get("content-type", "").split("/")[-1]  # gif / mp4 / webp
            return data, ext

@bot.event
async def on_ready():
    print("Connecté :", bot.user)

@bot.event
async def on_message(m):
    if m.author.bot:
        return

    match = URL_RE.search(m.content)
    if not match:
        return

    url = match.group(0)
    if not any(url.split("/")[2].endswith(d) for d in DOMAINS):
        return                                   # on ne touche qu’aux GIFs Tenor/Giphy

    data, ext = await download(url)
    if not data:
        return                                   # trop lourd ou erreur → on laisse

    try:
        await m.delete()
    except discord.Forbidden:
        pass

    file_name = f"gif.{ext or 'gif'}"
    file_obj  = discord.File(BytesIO(data), filename=file_name)

    embed = discord.Embed(color=discord.Color.dark_blue(), description="\u200b")
    embed.set_author(name=str(m.author), icon_url=m.author.display_avatar.url)
    embed.set_image(url=f"attachment://{file_name}")

    await m.channel.send(embed=embed, file=file_obj)

bot.run(os.getenv("DISCORD_TOKEN"))

