from discord.ext import commands


class Context(commands.Context):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def session(self):
        return self.bot.session  # type: ignore

    @property
    async def webhook(self):
        if self.channel.permissions_for(self.guild.me).manage_webhooks:
            webhooks = await self.channel.webhooks()

            if webhooks:
                webhook = webhooks[0]
            else:
                avatar = await self.bot.avatar.read()
                webhook = await self.channel.create_webhook(
                    name=self.bot.name, avatar=avatar
                )
            return webhook
