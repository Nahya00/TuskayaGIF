# bot.py
import discord, os, re, aiohttp

# ── Config ────────────────────────────────────────────────
TOKEN     = os.getenv("DISCORD_TOKEN")          # token bot
TENOR_KEY = os.getenv("TENOR_KEY")              # clé Tenor v2
GIF_SITES = ("tenor.com", "media.tenor.com",
             "giphy.com", "media.giphy.com")

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = discord.Client(intents=intents)

URL_RE = re.compile(r"https?://\S+")

# ── Helper : lien GIF via API Tenor ───────────────────────
async def tenor_gif(url: str) -> str | None:
    if not TENOR_KEY or "tenor.com" not in url:
        return None

    gif_id = url.rstrip("/").split("-")[-1]          # ...-<ID>
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

# ── Events ───────────────────────────────────────────────
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

    # On ne gère que Tenor / Giphy
    if not any(url.split("/")[2].endswith(d) for d in GIF_SITES):
        return

    # Tenor : on récupère le .gif direct
    direct = await tenor_gif(url) or url

    try:
        await m.delete()                       # nécessite “Gérer les messages”
    excep

