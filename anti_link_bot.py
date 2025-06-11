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

    gif_id = url.rstrip("/").split("-")[-1]        # …-<ID>
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

    # Tenor : essaie d’obtenir l’URL GIF directe
    direct = await tenor_gif(url) if "tenor.com" in url else url
    direct = direct or url    # fallback si API échoue

    try:
        await msg.delete()
    except discord.Forbidden:
        pass

    embed = discord.Embed(description="\u200b",
                          color=discord.Color.dark_blue())
    embed.set_author(name=str(msg.author),
                     icon_url=msg.author.display_avatar.url)
    embed.set_image(url=direct)

    try:
        await msg.channel.send(embed=embed)
    except discord.Forbidden:
        pass   # manque “Intégrer des liens” au bot ; ajoute-lui la permission

bot.run(TOKEN)

