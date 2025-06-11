import discord, os, re, aiohttp, json

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = discord.Client(intents=intents)

URL_RE = re.compile(r"https?://\S+")
WHITELIST = ("tenor.com", "giphy.com", "media.tenor.com", "media.giphy.com")

async def direct_gif(url: str) -> str | None:
    """Retourne l’URL GIF via oEmbed, ou None."""
    if "tenor.com" in url:
        oembed = f"https://tenor.com/oembed?url={url}"
    elif "giphy.com" in url:
        oembed = f"https://giphy.com/services/oembed?url={url}"
    else:
        return None

    async with aiohttp.ClientSession() as s:
        try:
            async with s.get(oembed, timeout=8) as r:
                if r.status != 200:
                    return None
                data = await r.json()
        except Exception:
            return None

    return data.get("url")            # champ “url” = GIF direct

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
        return                              # on ne gère que Tenor/Giphy

    gif_url = await direct_gif(url) or url  # fallback : lien d’origine

    try:
        await msg.delete()
    except discord.Forbidden:
        pass

    embed = discord.Embed(color=discord.Color.dark_blue())
    embed.set_author(name=str(msg.author), icon_url=msg.author.display_avatar.url)
    embed.set_image(url=gif_url)

    await msg.channel.send(embed=embed)

bot.run(os.getenv("DISCORD_TOKEN"))


