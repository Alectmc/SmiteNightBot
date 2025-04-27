from discord import app_commands
from discord.ext import commands

class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Adds the /grass command. Simply tells everyone in the server to touch grass.
    @app_commands.command(name="grass", description="Reminds everyone to touch grass")
    async def grass(self, interaction):
        await interaction.response.send_message("REMINDER: Touch grass.")

    # Adds the /grass command. Simply tells everyone in the server to drink water.
    @app_commands.command(name="water", description="Reminds everyone to drink water")
    async def water(self, interaction):
        await interaction.response.send_message("REMINDER: Drink water.")

async def setup(bot):
    await bot.add_cog(Misc(bot))