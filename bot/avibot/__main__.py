from avibot.core import Bot
from avibot.config import Config


def main() -> None:
    config = Config()
    avibot = Bot(config=config)
    avibot.load_extension("avibot.core.cog_manager")
    avibot.run()


if __name__ == "__main__":
    main()
