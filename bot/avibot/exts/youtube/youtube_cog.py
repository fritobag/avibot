import asyncio
from concurrent.futures import CancelledError
import re

from discord import utils
import discord

from avibot import Cog, command

from . import exceptions
from .livechat import LiveChatAsync


class Parser:
    VIDEOID_REGEX = re.compile(r"\"videoId\"\:\"([\w\d\-\_]+)\"")
    TITLE_REGEX = re.compile(
        r"{\"title\":{\"runs\":\[{\"text\":\"(?P<title>.{1,80})\"}\]\}"
    )
    INFO_REGEX = re.compile(r"\"dateText\"\:\{\"simpleText\":\"([\w\s,.]+)\"\}")
    COUNT_REGEX = re.compile(
        (
            r"{\"viewCount\":{\"runs\":\[\{\"text\":\"(\d*)\"\}"
            r",\{\"text\":\"([\w\s]*)\"\}\]\}"
        )
    )
    LIKES_REGEX = re.compile(r"\{\"label\":\"\d* likes\"\}\},\"simpleText\":\"(\d*)\"}")
    COUNTDOWN_REGEX = re.compile(
        (
            r"\"mainText\":\{\"runs\":\[\{\"text\":\"([\s\w]*)\"\}"
            r",\{\"text\":\"([\s\w]*)\"\}\]\}"
        )
    )

    def __init__(self, text: str):
        self.text = text
        self._info = ""
        self._is_live = False
        self.checked = False

    def title(self) -> str:
        if not self.is_live():
            return ""
        match = self.TITLE_REGEX.search(self.text)
        return match.group("title") if match else ""

    def is_live(self) -> bool:
        if self.checked:
            return self._is_live
        self.checked = True

        self._info = self.info()
        if self._info:
            self._is_live = True
            return True
        return False

    def info(self) -> str:
        if self._info:
            return self._info
        match = self.INFO_REGEX.search(self.text)
        return match.group(1) if match else ""

    def count(self) -> str:
        match = self.COUNT_REGEX.search(self.text)
        return match.group(1) + match.group(2) if match else "0 viewers"

    def likes(self) -> str:
        match = self.LIKES_REGEX.search(self.text)
        return match.group(1) if match else "0"

    def countdown(self) -> str:
        match = self.COUNTDOWN_REGEX.search(self.text)
        return match.group(1) + match.group(2) if match else ""

    def video_id(self) -> str:
        match = self.VIDEOID_REGEX.search(self.text)
        return match.group(1) if match else ""


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
        p = Parser(response_text)
        if not p.is_live():
            raise exceptions.StreamNotOnline
        return p.video_id()

    async def youtube_chat(self) -> None:
        """Youtube chat main loop."""
        while self.should_run:
            try:
                await self.start_chat()
            except Exception as e:
                self.logger.error(f"{type(e)}{str(e)}")

    async def start_chat(self) -> None:
        """Start new chat if possible."""
        if not self.webhooks:
            self.should_run = False
            self.cog_unload()

        try:
            video_id = await self.fetch_video_id()
        except exceptions.StreamNotOnline:
            self.logger.info("Stream is offline.")
            await asyncio.sleep(90)
            return

        for channel_id, webhook in self.webhooks.copy().items():
            await self.send_youtube_status(channel_id, webhook)

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
            self.logger.error("Youtube chat was cancelled.")

    async def on_message_handler(self, chat_data) -> None:
        """Handler for the on_message event."""
        for c in chat_data.items:
            if not c.message:
                return
            message = utils.escape_mentions(c.message)
            user = c.author
            username = user.name if not user.isChatModerator else user.name + " 🔧"
            for channel_id, webhook in self.webhooks.copy().items():
                await self.safe_send(
                    channel_id,
                    webhook,
                    content=message,
                    username=username,
                    avatar_url=user.imageUrl,
                )
            await chat_data.tick_async()

    async def safe_send(self, channel_id, webhook, *args, **kwargs) -> None:
        """Remove webhook if it fails."""
        try:
            await webhook.send(*args, **kwargs)
        except discord.errors.NotFound:
            self.webhooks.pop(channel_id)

    def cog_unload(self):
        """Unload cog."""
        self.should_run = False
        self.event.set()
        self.logger.info(f"Unload {self.__class__.__name__} cog.")

    def compose_youtube_status(self, response_text: str) -> str:
        """Compose youtube status."""
        p = Parser(response_text)

        info = p.info() if p.is_live() else "is too busy spamming his girlfriend"
        info = info[0].lower() + info[1:]
        countdown = p.countdown()
        countdown = f". {countdown}" if countdown else ""
        title = p.title() + "\n" if p.is_live() else ""
        likes = f", {p.likes()} likes"
        status = f" ({p.count()}{likes})" if p.is_live() else ""
        return (
            f"Avilo {info}{countdown}! {status}\n{title}"
            "Links: [youtube](<https://www.youtube.com/avilosoamaze/live>) "
            "and [twitch](<https://twitch.tv/avilo>)"
        )

    async def send_youtube_status(self, channel_id, webhook) -> None:
        """Send youtube status."""
        async with self.bot.session.get(self.URL, headers=self.HEADERS) as response:
            response_text = await response.text()

        message = self.compose_youtube_status(response_text)
        await self.safe_send(
            channel_id,
            webhook,
            content=message,
            username=self.bot.name,
            avatar_url=self.bot.avatar,
        )

    @command(aliases=["strim"])
    async def stream(self, ctx):
        """Check if avilo is streaming."""
        webhook = await ctx.webhook
        await self.send_youtube_status(None, webhook)
