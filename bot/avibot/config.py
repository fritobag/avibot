import os
from dataclasses import dataclass


@dataclass
class Bot:
    token: str = os.environ.get("BOT_TOKEN", "")
    complaint_email: str = os.environ.get("COMPLAINT_EMAIL", "")
    preload_ext = ["complaint", "youtube"]
    prefix = "!"


@dataclass
class Config:
    bot: Bot = Bot()
