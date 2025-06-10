import discord
import re
import os
import aiohttp
from bs4 import BeautifulSoup

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = discord.Client(intents=intents)

url_regex = re.compile(r'(https?://[^\s]+)')
whitelist_domains = ["tenor.com", "media.tenor.com", "giphy.com", "media.giphy.com"]

async def extract_direct_gif_url(url):
    # Utilise BeautifulSoup pour extraire l’URL du GIF direct depuis Tenor
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    gif_tag = soup.find("meta", property="og:image")
                    if gif_tag:
                        return gif_tag["content"]
        except Exception as e:
            print(f"Erreur d’extraction du GIF : {e}")
    return None

@bot.event
async def on_ready():
    print(f"Bot connecté en tant que {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    urls = url_regex.findall(message.content)
    for url in urls:
        domain = url.split('/')[2]

        if any(domain.endswith(allowed) for allowed in whitelist_domains):
            try:
                await message.delete()

                embed = discord.Embed(
                    description="**GIF détecté ✅**",
                    color=discord.Color.dark_blue()
                )
                embed.set_author(
                    name=str(message.author),
                    icon_url=message.author.avatar.url if message.author.avatar else message.author.default_avatar.url
                )

                gif_url = await extract_direct_gif_url(url)
                if gif_url:
                    embed.set_image(url=gif_url)
                else:
                    embed.description = "GIF détecté, mais non prévisualisable."

                await message.channel.send(embed=embed)
            except discord.Forbidden:
                print("🚫 Permissions manquantes.")
        else:
            try:
                await message.delete()

                embed = discord.Embed(
                    description="**Lien interdit supprimé.**",
                    color=discord.Color.red()
                )
                embed.set_author(
                    name=str(message.author),
                    icon_url=message.author.avatar.url if message.author.avatar else message.author.default_avatar.url
                )
                await message.channel.send(embed=embed, delete_after=5)
            except discord.Forbidden:
                print("🚫 Permissions manquantes.")
        break

bot.run(os.getenv("DISCORD_TOKEN"))


