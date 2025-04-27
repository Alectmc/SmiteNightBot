# Author: Alec Creasy
# File Name: quotes.py
# Description: Creates the Quotes cog to house all commands pertaining to the functionality
# that allows users to add and select random quotes.

from discord import app_commands
from discord.ext import commands
import os
import json
import random

#Create a Quotes class to be used as a Cog.
class Quotes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.quotes = [] # Create an empty list for the list of quotes.

        # If a quotes.json file exists, read in the quotes from the JSON file
        # and store them in the list.
        if os.path.exists("quotes.json"):
            with open("quotes.json") as f:
                self.quotes = json.load(f)

    # Adds the /addquote command. This command takes a quote and an author, gets the submitter's user ID, and saves the
    # submitter ID (user_id), the author of the quote, and the quote text and saves it as a dictionary entry. This is then
    # added to the quotes list as well as updates the quotes.json file so that quotes persist.
    @app_commands.command(name="addquote", description="Adds a quote to the bot")
    @app_commands.describe(quote_text="The quote that was said",
                           author="Who said it?")
    async def add_quote(self, interaction, quote_text:str, author:str):
        user_id = interaction.user.id
        author = author.strip().lower().capitalize()  # Remove whitespace and make the name the proper capitalization.

        new_quote = {
            "submitter_id": user_id,
            "author": author,
            "quote": quote_text
        }

        self.quotes.append(new_quote)

        with open("quotes.json", "w") as f:
            json.dump(self.quotes, f)

        await interaction.response.send_message(f"Quote added: {quote_text} - {author}", ephemeral=True)

    # Adds the /quote command. This command will display a random quote or, if an author is provided, display a quote
    # that a specific person has said if any exist, and send the quote to the channel the command was used for the
    # server to see. If no quotes are found or no quotes are found with the provided author, report that no quotes were
    # found to the user.
    @app_commands.command(name="quote", description="Displays a saved quote")
    @app_commands.describe(author="(Optional): Get a quote from a specific person!")
    async def quote(self, interaction, author:str=None):
        if not self.quotes:
            await interaction.response.send_message("No quotes found.", ephemeral=True)
            return

        if author:
            authored_quotes = [q for q in self.quotes if q.author == author.strip().lower().capitalize()]

            if not authored_quotes:
                await interaction.response.send_message(f"No quotes found for {author}.", ephemeral=True)
                return
            random_quote = random.choice(authored_quotes)
        else:
            random_quote = random.choice(self.quotes)

        submitter = await self.bot.fetch_user(random_quote['submitter_id'])
        submitter = submitter.mention

        await interaction.response.send_message(
            f"{random_quote['quote']} - {random_quote['author']}\nSubmitted by {submitter}")

#Setups cog for Quotes commands.
async def setup(bot):
        await bot.add_cog(Quotes(bot))