from webserver import keep_alive

import os
import discord
from discord.ext import tasks
import requests
from datetime import datetime, timedelta

# Bot configuration
GUILD_ID = 1321216357295067218  # Replace with your server (guild) ID
ROLE_ID = 1322723555770630205  # Replace with the role ID you want to ping
CHANNEL_ID = 1322724911080542268  # Replace with the channel ID where messages should be sent
URL_TO_CHECK = "https://ajcontent.akamaized.net/1705/ajclient.swf?v=1"  # Replace with the game's endpoint URL
CHECK_INTERVAL = 60  # Check interval in seconds

# Initialize the bot
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True
bot = discord.Client(intents=intents)

website_down = None  # Track website status
down_since = None  # Track the time when the website went down

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    check_website.start()  # Start the background task
    print("Started website status checks.")

@tasks.loop(seconds=CHECK_INTERVAL)
async def check_website():
    global website_down, down_since
    try:
        response = requests.get(URL_TO_CHECK, timeout=10)
        response.raise_for_status()  # Raise an error for HTTP errors
        if website_down:
            # If the site is back up
            website_down = False
            downtime = datetime.now() - down_since
            await notify_status_change("UP", downtime)
            down_since = None
    except requests.RequestException:
        if not website_down:
            # If the site is down
            website_down = True
            down_since = datetime.now()
            await notify_status_change("DOWN")

async def notify_status_change(status, downtime=None):
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        return
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return
    role = guild.get_role(ROLE_ID)

    if status == "UP":
        downtime_str = (
            f"Downtime Duration: {int(downtime.total_seconds() // 3600)}h "
            f"{int(downtime.total_seconds() % 3600 // 60)}m "
            f"{int(downtime.total_seconds() % 60)}s"
        )
        await channel.send(
            f"Animal Jam Classic is currently UP! ✅\n{downtime_str} {role.mention}"
        )
    elif status == "DOWN":
        await channel.send(
            f"Animal Jam Classic is currently DOWN! ❌\n{role.mention}"
        )

@bot.event
async def on_message(message):
    # Ensure the bot doesn't respond to itself
    if message.author == bot.user:
        return

    # Command: ?check
    if message.content.strip() == "?check":
        global website_down, down_since
        if website_down:
            # Calculate uptime since the site went down
            downtime = datetime.now() - down_since
            hours, remainder = divmod(downtime.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            downtime_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
            status_message = (
                f"Animal Jam Classic is currently DOWN! ❌\nDowntime: {downtime_str}"
            )
        else:
            status_message = "Animal Jam Classic is currently UP! ✅"

        await message.channel.send(status_message)

keep_alive()
TOKEN = os.environ.get("DISCORD_BOT_SECRET")
bot.run(TOKEN)