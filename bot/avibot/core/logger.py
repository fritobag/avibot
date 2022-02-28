import logging
import sys
from logging import handlers
import os

from .bot import Bot


def init_logger(bot: Bot, debug: bool = True):

    # set root logger level
    logging.getLogger().setLevel(logging.DEBUG)

    # setup discord logger
    discord_log = logging.getLogger("discord")
    discord_log.setLevel(logging.INFO)

    # setup bot logger
    avibot_log = logging.getLogger("avibot")
    avibot_log.setLevel(logging.INFO)

    # setup log directory
    log_path = os.path.join(bot.data_dir, "logs")
    if not os.path.exists(log_path):
        os.makedirs(log_path)

    # file handler factory
    def create_fh(file_name):
        fh_path = os.path.join(log_path, file_name)
        return handlers.RotatingFileHandler(
            filename=fh_path,
            encoding="utf-8",
            mode="a",
            maxBytes=400000,
            backupCount=20,
        )

    # set bot log formatting
    log_format = logging.Formatter(
        "%(asctime)s %(name)s %(levelname)s %(module)s %(funcName)s %(lineno)d: "
        "%(message)s",
        datefmt="[%d/%m/%Y %H:%M]",
    )

    # create avibot file handlers
    avibot_fh = create_fh("avibot.log")
    avibot_fh.setLevel(logging.INFO)
    avibot_fh.setFormatter(log_format)
    avibot_log.addHandler(avibot_fh)

    # create discord file handlers
    discord_fh = create_fh("discord.log")
    discord_fh.setLevel(logging.ERROR)
    discord_fh.setFormatter(log_format)
    discord_log.addHandler(discord_fh)

    console_std = sys.stdout if debug else sys.stderr

    # create discord avibot handlers
    avibot_console = logging.StreamHandler(console_std)
    avibot_console.setLevel(logging.INFO)
    avibot_console.setFormatter(log_format)
    avibot_log.addHandler(avibot_console)

    # create discord console handlers
    discord_console = logging.StreamHandler(console_std)
    discord_console.setLevel(logging.ERROR)
    discord_console.setFormatter(log_format)
    discord_log.addHandler(discord_console)

    bot.logger = avibot_log
