import logging
import os

import aiohttp
import discord
from discord.ext import commands

from avibot.config import Config
from avibot.core.context import Context


class Bot(commands.Bot):
    def __init__(self, config: Config, *kwargs):

        self.config = config
        self.prefix = config.bot.prefix
        self.preload_ext = config.bot.preload_ext

        self.core_dir = os.path.dirname(os.path.realpath(__file__))
        self.bot_dir = os.path.dirname(self.core_dir)
        self.ext_dir = os.path.join(self.bot_dir, "exts")
        self.data_dir = os.path.join(self.bot_dir, "data")

        self.logger = logging.getLogger("avibot.Bot")

        super().__init__(command_prefix=self.prefix, *kwargs)
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

    async def process_commands(self, message):
        """Process commands."""
        if message.author.bot:
            return
        ctx = await self.get_context(message, cls=Context)
        if not ctx.command:
            return
        await self.invoke(ctx)

    async def on_message(self, message):
        """Handle on_message event."""

        self.logger.info((message.author, message.content))
        await self.process_commands(message)

    async def on_connect(self):
        """Handle on_connect event."""
        self.logger.info("avibot connected")
        status = discord.Status.idle
        activity = discord.Game(name="Fighting")
        await self.change_presence(status=status, activity=activity)

    async def on_ready(self):
        """Handle on_ready event."""
        self.logger.info("avibot is ready")

        for ext in self.preload_ext:
            ext_name = "avibot.exts." + ext
            self.load_extension(ext_name)

    def run(self):
        """Overide run function."""
        super().run(self.config.bot.token)

    @property
    def name(self):
        return self.user.name

    @property
    def avatar(self):
        return self.user.avatar_url_as(static_format="png")


def command(*args, **kwargs):
    """A decorator that adds a function as a bot command."""

    def decorator(func):
        category = kwargs.get("category")
        func.command_category = category
        result = commands.command(*args, **kwargs)(func)
        return result

    return decorator


def group(*args, **kwargs):
    """A decorator that adds a function as a bot command group."""

    def decorator(func):
        category = kwargs.get("category")
        func.command_category = category
        result = commands.group(*args, **kwargs)(func)
        return result

    return decorator
