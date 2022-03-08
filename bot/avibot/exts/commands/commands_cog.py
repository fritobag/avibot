from discord import app_commands
import discord

from avibot import Cog


class Commands(Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command()
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(self, interaction: discord.Interaction, limit: int = 20):
        """Delete N last messages. (default: N = 20, max: N = 50)"""
        if not interaction.channel:
            return
        limit = limit if limit < 50 else 50
        await interaction.response.defer(ephemeral=True, thinking=True)
        deleted = await interaction.channel.purge(limit=limit, bulk=True)
        output = f"Done! {len(deleted)} messages were deleted."
        await interaction.followup.send(output, ephemeral=True)
