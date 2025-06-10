import discord
import re
import os

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = discord.Client(intents=intents)

url_regex = re.compile(r'https?://[^\s]+')
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
        embed = discord.Embed()
        embed.set_author(
            name=str(message.author),
            icon_url=message.author.avatar.url if message.author.avatar else message.author.default_avatar.url
        )

        if any(domain.endswith(allowed) for allowed in whitelist_domains):
            # GIF autorisé => envoyer embed bleu
            embed.description = "**GIF envoyé.**"
            embed.color = discord.Color.dark_blue()
            await message.channel.send(embed=embed, delete_after=5)
        else:
            # Lien interdit => supprimer + embed rouge
            try:
                await message.delete()
                embed.description = "**Les liens ne sont pas autorisés ici.**"
                embed.color = discord.Color.red()
                await message.channel.send(embed=embed, delete_after=5)
            except discord.Forbidden:
                print("🚫 Permissions manquantes pour supprimer ou envoyer un embed.")
            break

bot.run(os.getenv("DISCORD_TOKEN"))
