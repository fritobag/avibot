import pkgutil

from .cog_base import Cog
from avibot.core.bot import Bot


class CogManager(Cog):
    """Commands to add, remove and change cogs/extensions."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @property
    def available_exts(self):
        return [i[1] for i in pkgutil.iter_modules([self.bot.ext_dir])]

    async def load_extension(self, ctx, name: str, extension: str):
        ext_loc, ext = extension.rsplit(".", 1)
        if ext not in self.available_exts and ext_loc == "avibot.exts":
            return await ctx.error(f"Extension {name} not found")
        was_loaded = extension in ctx.bot.extensions
        try:
            if was_loaded:
                ctx.bot.reload_extension(extension)
            else:
                ctx.bot.load_extension(extension)
        except Exception as e:
            print(f"Error when loading extension {name}")
        else:
            print(f"Extension {name} {'reloaded' if was_loaded else 'loaded'}")


def setup(bot: Bot):
    bot.add_cog(CogManager(bot))
