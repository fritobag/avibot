import asyncio
from concurrent.futures import CancelledError
import re

from discord import utils
import discord

from avibot import Cog, command

from . import exceptions
from .livechat import LiveChatAsync


class Youtube(Cog):
    VIDEOID_REGEX = re.compile(r"\"videoId\"\:\"([\w\d\-\_]+)\"")
    INFO_REGEX = re.compile(r"\"dateText\"\:\{\"simpleText\":\"([\w\s,.]+)\"\}")
    HEADERS = {
        "accept-language": "en-US,en;q=0.5",
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/86.0.4240.198 Safari/537.36"
        ),
    }
    URL = "https://www.youtube.com/avilosoamaze/live"

    def __init__(self, bot):
        self.bot = bot
        self.should_run = True
        self.event = asyncio.Event()
        self.bot.loop.create_task(self._setup())
        self.channel_name = "youtube-chat"
        self.webhooks = dict()

    async def _setup(self) -> None:
        """Start all services."""
        await self.bot.wait_until_ready()
        await self._start_webhooks()
        await self.youtube_chat()

    async def _start_webhooks(self) -> None:
        """Collect all webhooks. Create new ones if needed."""
        self.webhooks.clear()
        items = [(g, c) for g in self.bot.guilds for c in g.text_channels]
        for guild, channel in items:
            if channel.name != self.channel_name:
                continue
            if not channel.permissions_for(guild.me).manage_webhooks:
                continue
            print(guild.name, channel.name)
            webhooks = await channel.webhooks()
            if webhooks:
                self.webhooks[channel.id] = webhooks[0]
            else:
                webhook = await channel.create_webhook(
                    name=self.bot.name, avatar=await self.bot.avatar.read()
                )
                self.webhooks[channel.id] = webhook

    async def fetch_video_id(self) -> str:
        """Fetch video id without the youtube api."""
        async with self.bot.session.get(self.URL, headers=self.HEADERS) as response:
            response_text = await response.text()
        match = self.INFO_REGEX.search(response_text)
        if match is None:
            raise exceptions.StreamNotOnline
        match = self.VIDEOID_REGEX.search(response_text)
        if match:
            return match.group(1)
        raise exceptions.VideoIDNotFound

    async def youtube_chat(self) -> None:
        """Youtube chat main loop."""
        while self.should_run:
            try:
                await self.start_chat()
            except Exception as e:
                print(f"{type(e)}{str(e)}")

    async def start_chat(self) -> None:
        """Start new chat if possible."""
        try:
            video_id = await self.fetch_video_id()
        except exceptions.StreamNotOnline:
            print("Stream is offline.")
            await asyncio.sleep(120)
            return
        livechat = LiveChatAsync(
            video_id,
            callback=self.on_message_handler,
            done_callback=lambda _: self.event.set(),
        )
        await self.event.wait()
        self.event.clear()
        try:
            livechat._task_finished()
        except CancelledError:
            print("Youtube chat was cancelled.")

    async def on_message_handler(self, chat_data) -> None:
        """Handler for the on_message event."""
        for c in chat_data.items:
            if not c.message:
                return
            message = utils.escape_mentions(c.message)
            user = c.author
            username = user.name if not user.isChatModerator else user.name + " 🔧"
            for channel_id, webhook in self.webhooks.copy().items():
                try:
                    await webhook.send(
                        content=message, username=username, avatar_url=user.imageUrl
                    )
                except discord.errors.NotFound:
                    self.webhooks.pop(channel_id)
            await chat_data.tick_async()

    def cog_unload(self):
        """Unload cog."""
        self.should_run = False
        self.event.set()

    @command()
    async def stream(self, ctx):
        """Check if avilo is streaming."""
        async with ctx.session.get(self.URL, headers=self.HEADERS) as response:
            response_text = await response.text()

        match = self.INFO_REGEX.search(response_text)
        if match:
            info = match.group(1)
            info = info[0].lower() + info[1:]
        else:
            info = "is too busy spamming his girlfriend"

        webhook = await ctx.webhook
        await webhook.send(
            (
                f"Avilo {info}!\nLinks: "
                "[youtube](<https://www.youtube.com/avilosoamaze/live>) "
                "and [twitch](<https://twitch.tv/avilo>)"
            ),
            username=self.bot.name,
            avatar_url=self.bot.avatar,
        )
