import aiohttp
import discord
from discord.ext import commands
from avibot.config import Config


class Bot(commands.Bot):
    def __init__(self, config: Config, *kwargs):
        super().__init__(
            command_prefix="!",
            *kwargs,
        )
        self.config = config
        self.loop.run_until_complete(self._create_session())

    async def _create_session(self):
        """Create a main aiohttp session."""
        self.session = aiohttp.ClientSession(loop=self.loop)

    async def shutdown(self):
        """Implement shutdown logic."""
        await self.logout()
        if self.session:
            await self.session.close()

    async def close(self):
        """Implement close logic."""
        if self.session:
            await self.session.close()
        await super().close()

    async def on_message(self, message):
        """Handle on_message event."""
        await self.process_commands(message)

    async def on_connect(self):
        """Handle on_connect event."""
        print("avibot connected.")
        status = discord.Status.idle
        activity = discord.Game(name="Fighting")
        await self.change_presence(status=status, activity=activity)

    async def on_ready(self):
        """Handle on_ready event."""
        print("avibot ready.")

    def run(self):
        """Overide run function."""
        super().run(self.config.bot.token)
