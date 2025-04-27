# Author: Alec Creasy
# File Name: events.py
# Description: Creates a Cog to listen for events, in particular, when a member joins the server.

from discord import utils
from discord.ext import commands

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Triggers when a member joins the server. Gets the welcome channel (if it exists), and sends a welcome
    # message to the welcome channel mentioning the user. In the API, servers are referenced as guilds.
    @commands.Cog.listener()
    async def on_member_join(self, member):
        welcome_channel = utils.get(member.guild.channels, name='welcome')
        if welcome_channel:
            await welcome_channel.send(f"Everyone give a HUGE welcome to this new pal: {member.mention}!")

# Setups Cog to listen for on_member_join event.
async def setup(bot):
    await bot.add_cog(Events(bot))