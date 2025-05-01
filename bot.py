# Author: Alec Creasy
# File Name: bot.py
# Description: Creates a discord bot to be used in the Smite Night Server.
# Has functionality to handle and save quotes, send joke reminder, send server ping,
#and welcome new users.

from discord import Intents, Game
import discord.ext.commands as commands
import dotenv
from typing import Final
import os

# Load environment with token and store it in a constant.
dotenv.load_dotenv()
TOKEN: Final[str] = os.getenv("TOKEN")

# Set intents, as well as enable the members intent.
# We need these enabled to detect new users.
intents = Intents.default()
intents.members = True
intents.message_content = True

# Initialize the bot for slash commands.
bot = commands.Bot(command_prefix='/', intents=intents)

# Triggers when the bot is ready. Prints to the console that the user is online, syncs the commands, and sets the
# activity to "/help if ya need something".
@bot.event
async def on_ready():
    print(f"SmiteNightBot is now online as {bot.user}")

    activity = Game("/help if ya need something")
    await bot.change_presence(activity=activity)

    await bot.load_extension("cogs.events")
    await bot.load_extension("cogs.utility")
    await bot.load_extension("cogs.quotes")
    await bot.load_extension("cogs.misc")
    await bot.load_extension("cogs.wordle")
    print("COGS Loaded!")

    await bot.tree.sync()
    print("Commands synced!")

bot.run(token=TOKEN)