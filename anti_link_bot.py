import discord, os, re, aiohttp

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = discord.Client(intents=intents)

URL_RE = re.compile(r"https?://\S+")
WHITELIST = ("tenor.com", "media.tenor.com")
TENOR_KEY = os.getenv("TENOR_KEY")     # <-- ta clé

async def tenor_direct(url: str) -> str | None:
    """Extrait l’ID du GIF et appelle l’API Tenor pour un lien .gif direct."""
    if not TENOR_KEY:
        return None

    # URL Tenor : https://tenor.com/view/xxx-<ID>
    try:
        gif_id = url.rstrip("/").split("-")[-1]
        api = (
            f"https://tenor.googleapis.com/v2/posts"
            f"?ids={gif_id}&key={TENOR_KEY}&media_filter=gif"
        )
    except Exception:
        return None

    async with aiohttp.ClientSession() as s:
        try:
            async with s.get(api, timeout=8) as r:
                if r.status != 200:
                    return None
                data = await r.json()
        except Exception:
            return None

    media = (
        data.get("results", [{}])[0]
            .get("media_formats", {})
            .get("gif", {})
            .get("url")
    )
    return media         # None si rien trouvé

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
    domain = url.split("/")[2]

    if domain.endswith(WHITELIST):
        # --- Tenor : passe par l’API pour le .gif direct ---
        gif_url = await tenor_direct(url) or url

        try:
            await msg.delete()
        except discord.Forbidden:
            pass

        embed = discord.Embed(
            description="\u200b",              # invisible → garde le cadre
            color=discord.Color.dark_blue()
        )
        embed.set_author(
            name=str(msg.author),
            icon_url=msg.author.display_avatar.url
        )
        embed.set_image(url=gif_url)

        await msg.channel.send(embed=embed)

    else:
        # Lien non autorisé → on ignore ou on supprime, à toi de voir
        return

bot.run(os.getenv("DISCORD_TOKEN"))

