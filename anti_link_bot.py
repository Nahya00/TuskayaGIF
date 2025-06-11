import discord, os, re, aiohttp, json

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = discord.Client(intents=intents)

URL_RE = re.compile(r"https?://\S+")
WHITELIST = ("tenor.com", "giphy.com", "media.tenor.com", "media.giphy.com")

async def get_direct(url: str) -> str:
    """Retourne l’URL GIF direct via oEmbed, ou l’URL d’origine."""
    if "tenor.com" in url:
        oembed = f"https://tenor.com/oembed?url={url}"
    elif "giphy.com" in url:
        oembed = f"https://giphy.com/services/oembed?url={url}"
    else:
        return url

    async with aiohttp.ClientSession() as s:
        try:
            async with s.get(oembed, timeout=8) as r:
                if r.status != 200:
                    return url
                data = await r.json()
        except Exception:
            return url

    return data.get("url", url)

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
    if not any(url.split("/")[2].endswith(d) for d in WHITELIST):
        return  # on ne s’occupe que des GIF Tenor/Giphy

    direct = await get_direct(url)

    # supprime le message d’origine
    try:
        await msg.delete()
    except discord.Forbidden:
        pass

    # le bot renvoie juste le lien => Discord fait l’aperçu tout seul
    await msg.channel.send(f"{msg.author.mention} {direct}")

bot.run(os.getenv("DISCORD_TOKEN"))



