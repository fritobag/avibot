import discord

from avibot import logger
from avibot.config import Config
from avibot.core import Bot


def main() -> None:
    config = Config()

    intents = discord.Intents.all()
    avibot = Bot(config=config, intents=intents)

    logger.init_logger(avibot)
    avibot.run()


if __name__ == "__main__":
    main()
