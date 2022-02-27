import os
from dataclasses import dataclass


@dataclass
class Bot:
    token: str = os.environ.get("BOT_TOKEN", "")


@dataclass
class Config:
    bot: Bot = Bot()
