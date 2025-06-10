import discord
import re
import os

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = discord.Client(intents=intents)

url_regex = re.compile(r'(https?://[^\s]+)')
whitelist_domains = ["tenor.com", "media.tenor.com", "giphy.com", "media.giphy.com"]

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
                embed.set_image(url=url)

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

