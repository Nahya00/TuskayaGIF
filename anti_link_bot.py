# bot.py
import discord
import os
import re

# ─── configuration de base ────────────────────────────
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True          # nécessaire pour lire le contenu

bot = discord.Client(intents=intents)

GIF_DOMAINS = ("tenor.com", "giphy.com", "media.tenor.com", "media.giphy.com")
URL_RE      = re.compile(r"https?://\S+")

@bot.event
async def on_ready():
    print(f"Bot connecté : {bot.user}")

@bot.event
async def on_message(msg):
    # ignore les bots et les messages sans lien
    if msg.author.bot:
        return
    match = URL_RE.search(msg.content)
    if not match:
        return

    url = match.group(0)
    # on ne garde que Tenor / Giphy
    if not any(url.split('/')[2].endswith(d) for d in GIF_DOMAINS):
        return

    # ── 1. supprime le message d'origine ─────────────────
    try:
        await msg.delete()              # le bot doit avoir "Gérer les messages"
    except discord.Forbidden:
        pass

    # ── 2. renvoie l'embed avec le GIF ───────────────────
    embed = discord.Embed(description="\u200b",  # caractère invisible ⇒ cadre bleu
                          color=discord.Color.dark_blue())
    embed.set_author(name=str(msg.author),
                     icon_url=msg.author.display_avatar.url)
    embed.set_image(url=url)             # Discord affiche le GIF

    await msg.channel.send(embed=embed)  # le bot doit avoir "Intégrer des liens"

# ─── lance le bot ──────────────────────────────────────
bot.run(os.getenv("DISCORD_TOKEN"))

