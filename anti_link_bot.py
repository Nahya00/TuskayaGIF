# bot.py
import discord, os, re, aiohttp

TOKEN      = os.getenv("DISCORD_TOKEN")
TENOR_KEY  = os.getenv("TENOR_KEY")          # clé Tenor v2
GIF_DOMAINS = ("tenor.com", "media.tenor.com",
               "giphy.com", "media.giphy.com")

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True      # ← OBLIGATOIRE (et activé dans le portail)
bot = discord.Client(intents=intents)

URL_RE = re.compile(r"https?://\S+")

# ───── helper : URL .gif via l’API Tenor ─────────────────────────────────
async def tenor_gif(url: str) -> str | None:
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

# ───── on_message ───────────────────────────────────────────────────────
@bot.event
async def on_message(msg):
    if msg.author.bot:
        return

    # 1) lien dans le texte
    url = None
    m = URL_RE.search(msg.content)
    if m:
        url = m.group(0)

    # 2) sinon cherche dans les embeds (GIF “Favoris” mobile/desktop)
    if not url and msg.embeds:
        for emb in msg.embeds:
            # « gifv » ou « image » : emb.url pointe vers Tenor/Giphy
            if emb.url:
                url = emb.url
            # parfois seul thumbnail.url contient le lien Tenor
            elif emb.thumbnail and emb.thumbnail.url:
                url = emb.thumbnail.url
            if url:
                break

    if not url:
        return                                # rien à faire

    if not any(url.split('/')[2].endswith(d) for d in GIF_DOMAINS):
        return                                # pas un domaine GIF accepté

    # Tenor ➜ transforme en .gif direct via l’API
    final = await tenor_gif(url) if "tenor.com" in url else url
    final = final or url                     # fallback

    # supprime le message d’origine
    try:
        await msg.delete()                   # nécessite « Gérer les messages »
    except discord.Forbidden:
        return

    # renvoie l’embed
    embed = discord.Embed(description="\u200b", color=discord.Color.dark_blue())
    embed.set_author(name=str(msg.author),
                     icon_url=msg.author.display_avatar.url)
    embed.set_image(url=final)

    await msg.channel.send(embed=embed)      # nécessite « Intégrer des liens »

# ───── lancement ────────────────────────────────────────────────────────
bot.run(TOKEN)


