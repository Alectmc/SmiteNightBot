# Author: Alec Creasy
# File Name: bot.py
# Description: Creates a discord bot to be used in the Smite Night Server.
# Has functionality to handle and save quotes, send joke reminder, send server ping,
#and welcome new users.

from discord import Intents, Message, Member, Game, app_commands, utils
import discord.ext.commands as commands
import dotenv
import random
from typing import Final
import os
import json

# Load environment with token and store it in a constant.
dotenv.load_dotenv()
TOKEN: Final[str] = os.getenv("TOKEN")

# Set intents, as well as enable the members intent.
# We need these enabled to detect new users.
intents = Intents.default()
intents.members = True

# Instatiate the bot for slash commands.
bot = commands.Bot(command_prefix='/', intents=intents)

# Create an empty list for the list of quotes.
quotes = []

# If a quotes.json file exists, read in the quotes from the JSON file
# and store them in the list.
if os.path.exists("quotes.json"):
    with open("quotes.json") as f:
        quotes = json.load(f)

# Triggers when a member joins the server. Gets the welcome channel (if it exists), and sends a welcome
# message to the welcome channel mentioning the user.
@bot.event
async def on_member_join(member):
    welcome_channel = utils.get(member.guild.channels, name='welcome')
    if welcome_channel:
        await welcome_channel.send(f"Everyone give a HUGE welcome to this new pal: {member.mention}!")

# Triggers when the bot is ready. Prints to the console that the user is online, syncs the commands, and sets the
# activity to "/help if ya need something".
@bot.event
async def on_ready():
    print(f"Smite Night Bot is now online as {bot.user}")

    await bot.tree.sync()
    print("Commands synced!")

    activity = Game("/help if ya need something")
    await bot.change_presence(activity=activity)

# Adds the /ping command. The ping command simply responds to the user with the ping to the server.
@bot.tree.command(name="ping", description="Replies with latency to server")
async def ping(interaction):
    await interaction.response.send_message(f"Pong! {round(bot.latency * 1000)}ms", ephemeral=True)

# Adds the /help command. Responds to the user with a list of commands.
@bot.tree.command(name="help", description="Displays the list of commands")
async def help(interaction):
    help_message = ("Available Commands:\n\n"
                    "/help: Displays a list of commands\n"
                    "/ping: Replies with latency to server"
                    "/addquote: Adds a quote\n"
                    "/quote: displays a saved quote\n"
                    "/grass: Reminds everyone to touch grass\n"
                    "/water: Reminds everyone to drink water\n")
    await interaction.response.send_message(help_message, ephemeral=True)

# Adds the /addquote command. This command takes a quote and an author, gets the submitter's user ID, and saves the
# submitter ID (user_id), the author of the quote, and the quote text and saves it as a dictionary entry. This is then
# added to the quotes list as well as updates the quotes.json file so that quotes persist.
@bot.tree.command(name="addquote", description="Adds a quote to the bot")
@app_commands.describe(quote_text="The quote that was said",
                       author="Who said it?")
async def add_quote(interaction, quote_text, author):
    user_id = interaction.user.id
    author = author.strip().lower().capitalize() #Remove whitespace and make the name the proper capitalziation.

    new_quote = {
        "submitter_id": user_id,
        "author": author,
        "quote": quote_text
    }

    quotes.append(new_quote)

    with open("quotes.json", "w") as f:
        json.dump(quotes, f)

    await interaction.response.send_message(f"Quote added: {quote} - {author}", ephemeral=True)

# Adds the /quote command. This command will display a random quote or, if an author is provided, display a quote
# that a specific person has said if any exist, and send the quote to the channel the command was used for the
# server to see. If no quotes are found or no quotes are found with the provided author, report that no quotes were
# found to the user.
@bot.tree.command(name="quote", description="Displays a saved quote")
@app_commands.describe(author="(Optional): Get a quote from a specific person!")
async def quote(interaction, author=None):
    if not quotes:
        await interaction.response.send_message("No quotes found.", ephemeral=True)
        return

    if author:
        authored_quotes = [q for q in quotes if q.author == author.strip().lower().capitalize()]

        if not authored_quotes:
            await interaction.response.send_message(f"No quotes found for {author}.", ephemeral=True)
            return
        random_quote = random.choice(authored_quotes)
    else:
        random_quote = random.choice(quotes)

    submitter = await bot.fetch_user(random_quote['submitter_id'])
    submitter = submitter.mention

    await interaction.response.send_message(f"{random_quote['quote']} - {random_quote['author']}\nSubmitted by {submitter}")

# Adds the /grass command. Simply tells everyone in the server to touch grass.
@bot.tree.command(name="grass", description="Reminds everyone to touch grass")
async def grass(interaction):
    await interaction.response.send_message("REMINDER: Touch grass.")

# Adds the /grass command. Simply tells everyone in the server to drink water.
@bot.tree.command(name="water", description="Reminds everyone to drink water")
async def water(interaction):
    await interaction.response.send_message("REMINDER: Drink water.")