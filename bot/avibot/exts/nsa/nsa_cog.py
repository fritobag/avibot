from avibot import Cog
from discord import app_commands
from typing import Optional
import discord
import avibot.core.database as db
from datetime import timezone, datetime
import asyncio
import re
import json
import collections
import itertools

EMOJI_REGEX = re.compile(r"(<a?:.+?:[0-9]{15,21}>)")


class Message(db.Base):
    __tablename__ = "message"
    message_id = db.Column(db.BigInteger, primary_key=True)
    guild_id = db.Column(db.BigInteger)
    channel_id = db.Column(db.BigInteger)
    author_id = db.Column(db.BigInteger)
    created_at = db.Column(db.BigInteger)
    content = db.Column(db.String)
    clean_content = db.Column(db.String)
    emojis = db.Column(db.ARRAY(db.String))
    attachments = db.Column(db.ARRAY(db.String))
    is_edited = db.Column(db.Boolean)
    is_deleted = db.Column(db.Boolean)
    is_bot = db.Column(db.Boolean)
    webhook_id = db.Column(db.BigInteger)
    embeds = db.Column(db.ARRAY(db.JSONB))

    def __repr__(self):
        return f"Message(id={self.message_id}, content={self.content})"


def find_emojis(text):
    """returns a list of emojis if any"""
    return EMOJI_REGEX.findall(text)


def parse_message(message):
    created_at = int(message.created_at.replace(tzinfo=timezone.utc).timestamp())
    attachments = [a.url for a in message.attachments]
    embeds = [json.dumps(e.to_dict()) for e in message.embeds]
    return Message(
        message_id=message.id,
        created_at=created_at,
        is_edited=False,
        is_deleted=False,
        author_id=message.author.id,
        channel_id=message.channel.id,
        guild_id=message.guild.id if message.guild else None,
        content=message.content,
        clean_content=message.clean_content,
        embeds=embeds,
        is_bot=message.author.bot,
        webhook_id=message.webhook_id,
        emojis=find_emojis(message.content),
        attachments=attachments,
    )


async def history_chunk(channel, n=2000, limit=None, timestamp=None, oldest_first=None):
    chunk = []
    async for message in channel.history(
        limit=limit, after=timestamp, oldest_first=oldest_first
    ):
        chunk.append(message)
        if len(chunk) == n:
            yield chunk
            chunk = []
    if len(chunk) > 0:
        yield chunk


class Nsa(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.event = asyncio.Event()
        self.bot.loop.create_task(self._update())

    async def _update(self):
        await self.bot.wait_until_ready()
        self.event.clear()
        self.logger.info("Started updating")
        try:
            async with self.bot.dbi.get_session() as s:
                statement = db.select(
                    Message.channel_id, db.func.max(Message.created_at)
                ).group_by(Message.channel_id)
                query = await s.execute(statement)
            data = query.all()
            last_messages = {r[0]: datetime.utcfromtimestamp(r[1] + 1) for r in data}

            channels = [c for guild in self.bot.guilds for c in guild.text_channels]
            for channel in channels:
                count = 0
                timestamp = last_messages.get(channel.id, None)
                async for message_chunk in history_chunk(channel, timestamp=timestamp):
                    count = count + len(message_chunk)
                    self.logger.info(f"{count} - {channel.name}")
                    async with self.bot.dbi.get_session() as s:
                        for message in message_chunk:
                            s.add(parse_message(message))
                        await s.commit()
        finally:
            self.logger.info("Finished updating.")
            self.event.set()

    @app_commands.command()
    async def find(self, interaction: discord.Interaction, *, text: str):

        if not (interaction.guild and interaction.channel):
            return

        await interaction.response.defer(ephemeral=False, thinking=True)
        async with self.bot.dbi.get_session() as s:
            statement = db.text(
                """SELECT author_id, (SUM(LENGTH(LOWER(content)))
                    -SUM(LENGTH(replace(LOWER(content),LOWER(:text),''))))/LENGTH(:text)
                    AS times from message
                    WHERE is_bot = false AND guild_id = :guild_id
                    AND channel_id = :channel_id AND is_deleted=false
                    AND LOWER(content) NOT LIKE '_find%'
                    GROUP BY author_id ORDER BY times DESC;"""
            )
            query = await s.execute(
                statement,
                {
                    "text": text,
                    "guild_id": interaction.guild.id,
                    "channel_id": interaction.channel.id,
                },
            )
            results = [(r[0], r[1]) for r in query.all() if r[1] > 0]
            statement = db.text(
                """SELECT author_id, message_id, channel_id from message
                    WHERE LOWER(content) LIKE LOWER(:text)
                    AND LOWER(content) NOT LIKE '_find%'
                    AND is_bot = false AND guild_id = :guild_id
                    AND is_deleted=false ORDER BY created_at DESC;"""
            )
            # TODO: fix the statement bellow
            # statement = (
            #     db.select(Message.author_id, Message.message_id, Message.channel_id)
            #     .filter(Message.content.notlike("_find%"))
            #     .where(Message.is_bot == False)  # noqa: all
            #     .where(Message.is_deleted == False)  # noqa: all
            #     .where(Message.guild_id == interaction.guild.id)
            #     .where(Message.channel_id == interaction.channel.id)
            #     .order_by(Message.created_at.desc())
            # )
            query = await s.execute(
                statement, {"text": f"%{text}%", "guild_id": interaction.guild.id}
            )
            record = query.first()

            output = "**Find**: {}\nMembers: ".format(text)
            for author_id, quantity in results[:7]:
                user = self.bot.get_user(int(author_id))
                if user:
                    output += "{0.display_name}: {1}x\t".format(user, quantity)
                else:
                    try:
                        user = await self.bot.fetch_user(int(author_id))
                        output += "✞{0.display_name}: {1}x\t".format(user, quantity)
                    except (discord.NotFound, discord.HTTPException):
                        continue

            if record:
                message_id, channel_id = record[1], record[2]
                try:
                    channel = self.bot.get_channel(channel_id)
                    message = await channel.fetch_message(message_id)
                    output += "\nLast sent by [{}](<{}>)".format(
                        message.author.name, message.jump_url
                    )
                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                    pass

            await interaction.followup.send(output, ephemeral=False)

    @app_commands.command()
    async def emojis(
        self, interaction: discord.Interaction, member: Optional[discord.Member]
    ):
        """List most used emojis. (Default: server, Optional: member)"""
        if not interaction.guild:
            return
        await interaction.response.defer(ephemeral=False, thinking=True)
        async with self.bot.dbi.get_session() as s:
            statement = (
                db.select(Message.emojis)
                .distinct(Message.message_id)
                .where(Message.is_deleted == False)  # noqa: all
                .where(Message.is_bot == False)  # noqa: all
                .where(Message.guild_id == interaction.guild.id)
                .order_by(Message.message_id.asc(), Message.created_at.asc())
            )
            if member:
                statement = statement.where(Message.author_id == member.id)
            query = await s.execute(statement)
        data = list(filter(lambda x: x, query.scalars().all()))
        sort_orders = sorted(
            collections.Counter(list(itertools.chain(*data))).items(),
            key=lambda x: x[1],
            reverse=True,
        )
        if member:
            output = f"**{member.display_name}'s emojis**: \n"
        else:
            output = f"**{interaction.guild.name}'s emojis**: \n"
        if sort_orders:
            output += " ".join([f"{item[0]}x{item[1]}" for item in sort_orders[:10]])
        else:
            output += "No emojis found."
        await interaction.followup.send(output, ephemeral=False)

    @Cog.listener()
    async def on_message(self, message):
        await self.event.wait()
        async with self.bot.dbi.get_session() as s:
            s.add(parse_message(message))
            await s.commit()

    @Cog.listener()
    async def on_raw_message_delete(self, payload):
        await self.event.wait()
        async with self.bot.dbi.get_session() as s:
            await s.execute(
                db.update(Message)
                .where(Message.message_id == payload.message_id)
                .values(is_deleted=True)
            )
            await s.commit()

    @Cog.listener()
    async def on_raw_bulk_message_delete(self, payload):
        await self.event.wait()
        async with self.bot.dbi.get_session() as s:
            conds = [Message.message_id == m_id for m_id in payload.message_ids]
            await s.execute(
                db.update(Message).where(db.or_(*conds)).values(is_deleted=True)
            )
            await s.commit()

    # TODO: on_edit
