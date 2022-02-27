import logging

from discord.ext.commands import Cog


class Cog(Cog):
    _is_base = True

    def __new__(cls, bot, *args, **kwargs):
        instance = super().__new__(cls, *args, **kwargs)

        def run_cog_init(klass):
            for base in klass.__bases__:
                if base is object:
                    return
                elif base._is_base:
                    base.__init__(instance, bot)
                else:
                    run_cog_init(base)

        run_cog_init(instance.__class__)
        return instance

    def __init_subclass__(cls):
        cls._is_base = False

    def __init__(self, bot):
        self.bot = bot
        module = self.__class__.__module__
        cog = self.__class__.__name__
        log_name = f"{module}.{cog}"
        self.logger = logging.getLogger(log_name)
