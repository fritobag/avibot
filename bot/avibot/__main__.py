from avibot.core import Bot
from avibot.config import Config
import asyncio


def main() -> None:
    config = Config()
    avibot = Bot(config=config)
    avibot.run()


if __name__ == "__main__":
    main()
