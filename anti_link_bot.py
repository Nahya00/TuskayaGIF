import discord
from discord.ext import commands
import re
import os
import aiohttp

TOKEN = os.getenv("DISCORD_TOKEN")
TENOR_API_KEY = os.getenv("TENOR_API_KEY")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="§", intents=intents)

url_regex = re.compile(r'https?://[^\s]+')

async def get_tenor_gif_url(url):
    async with aiohttp.ClientSession() as session:
        match = re.search(r'-([0-9]+)$', url)
        if not match:
            return None
        gif_id = match.group(1)
        api_url = f"https://tenor.googleapis.com/v2/posts?ids={gif_id}&key={TENOR_API_KEY}"
        async with session.get(api_url) as response:
            if response.status == 200:
                data = await response.json()
                try:
                    return data["results"][0]["media_formats"]["gif"]["url"]
                except (KeyError, IndexError):
                    return None
            return None

@bot.event
async def on_ready():
    print(f"✅ Bot connecté en tant que {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    urls = url_regex.findall(message.content)
    if urls:
        for url in urls:
            if "tenor.com" in url:
                try:
                    await message.delete()
                    gif_url = await get_tenor_gif_url(url)
                    if gif_url:
                        embed = discord.Embed(color=discord.Color.blue())
                        embed.set_image(url=gif_url)
                        embed.set_footer(text=f"GIF partagé par {message.author.display_name}")
                        await message.channel.send(embed=embed)
                    else:
                        print("❗ Impossible de récupérer le lien direct du GIF.")
                except Exception as e:
                    print(f"Erreur lors du traitement du GIF Tenor : {e}")
                break

    await bot.process_commands(message)

bot.run(TOKEN)

