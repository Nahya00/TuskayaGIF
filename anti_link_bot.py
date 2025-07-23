import os, re, mimetypes, aiohttp, discord
from io import BytesIO
from discord import File, Embed

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
TENOR_KEY     = os.getenv("TENOR_KEY")
MAX_BYTES     = 8 * 1024 * 1024
DOMAINS       = ("tenor.com", "media.tenor.com","giphy.com","media.giphy.com")

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = discord.Client(intents=intents)

URL_RE = re.compile(r"https?://\S+")

async def fetch_media(url:str):
    async with aiohttp.ClientSession() as s:
        try:
            async with s.get(url, timeout=10) as r:
                if r.status!=200:
                    return None,None
                ctype=r.headers.get("content-type","").split(";")[0]
                if not (ctype.startswith("image/") or ctype=="video/mp4"):
                    return None,None
                data=await r.read()
                if len(data)>MAX_BYTES:
                    return None,None
                ext=mimetypes.guess_extension(ctype) or ".gif"
                return data, ext.lstrip(".")
        except Exception:
            return None,None

def extract_link(msg:discord.Message)->str|None:
    m=URL_RE.search(msg.content or "")
    if m and any(m.group(0).split("/")[2].endswith(d) for d in DOMAINS):
        return m.group(0)
    for emb in msg.embeds:
        if emb.url and any(emb.url.split("/")[2].endswith(d) for d in DOMAINS):
            return emb.url
        if emb.thumbnail and emb.thumbnail.url:
            t=emb.thumbnail.url
            if any(t.split("/")[2].endswith(d) for d in DOMAINS):
                return t
    return None

@bot.event
async def on_ready():
    print("Connected:", bot.user)

@bot.event
async def on_message(msg:discord.Message):
    if msg.author.bot: return
    url=extract_link(msg)
    if not url: return
    data,ext = await fetch_media(url)
    embed=Embed(description="\u200b", color=0x2F3136)
    embed.set_author(name=str(msg.author), icon_url=msg.author.display_avatar.url)
    files=None
    if data:
        fname=f"file.{ext}"
        files=[File(BytesIO(data), filename=fname)]
        embed.set_image(url=f"attachment://{fname}")
    else:
        embed.set_image(url=url)
    sent=await msg.channel.send(embed=embed, files=files)
    try:
        await msg.delete()
    except discord.Forbidden:
        pass

bot.run(DISCORD_TOKEN)

