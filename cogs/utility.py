# Author: Alec Creasy
# File Name: utility.py
# Description: Creates a Cog for the utility commands: /help and /ping.

from discord import app_commands
from discord.ext import commands

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # # Adds the /ping command. The ping command simply responds to the user with the ping to the server.
    @app_commands.command(name="ping", description="Replies with latency to server")
    async def ping(self, interaction):
        await interaction.response.send_message(f"Pong! {round(self.bot.latency * 1000)}ms", ephemeral=True)

    # Adds the /help command. Responds to the user with a list of commands.
    @app_commands.command(name="help", description="Displays the list of commands")
    async def help(self, interaction):
        help_message = ("Available Commands:\n\n"
                        "/help: Displays a list of commands\n"
                        "/ping: Replies with latency to server\n"
                        "/addquote: Adds a quote\n"
                        "/quote: displays a saved quote\n"
                        "/wordle: Initiates a game of wordle (must be in the #wordle channel to start the game)\n"
                        "/grass: Reminds everyone to touch grass\n"
                        "/water: Reminds everyone to drink water\n")
        await interaction.response.send_message(help_message, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Utility(bot))