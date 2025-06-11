import discord, os, re, aiohttp

# ─── Config ────────────────────────────────────────────────────────────
TOKEN      = os.getenv("DISCORD_TOKEN")      # token du bot
TENOR_KEY  = os.getenv("TENOR_KEY")          # ta clé Tenor v2
INTENTS    = discord.Intents.default()
INTENTS.messages = True
INTENTS.message_content = True

bot = discord.Client(intents=INTENTS)

URL_RE    = re.compile(r"https?://\S+")
WHITELIST = ("tenor.com", "media.tenor.com",   # Tenor
             "giphy.com", "media.giphy.com")   # Giphy (laisse passer)

# ─── Helper : lien .gif via API Tenor ──────────────────────────────────
async def tenor_gif(url: str) -> str | None:
    """Retourne le .gif direct depuis l’API Tenor ; None si échec."""
    if not TENOR_KEY:
        return None                           # pas de clé → on saute
    # URL Tenor = …-<ID>   ⇒ on récupère l’ID numeric
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

# ─── Events ────────────────────────────────────────────────────────────
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

    # ─── Lien Tenor / Giphy autorisé ────────────────────────────────
    if domain.endswith(WHITELIST):

        # Si Tenor → essaie d’obtenir le .gif via l’API
        direct_url = await tenor_gif(url) if "tenor.com" in domain else url
        direct_url = direct_url or url   # fallback

        try:
            await msg.delete()
        except discord.Forbidden:
            pass

        embed = discord.Embed(description="\u200b",   # invisible → cadre bleu
                              color=discord.Color.dark_blue())
        embed.set_author(name=str(msg.author),
                         icon_url=msg.author.display_avatar.url)
        embed.set_image(url=direct_url)

        await msg.channel.send(embed=embed)

    # ─── Autres liens → tu peux les supprimer ou les ignorer ──────────
    else:
        return

bot.run(TOKEN)
