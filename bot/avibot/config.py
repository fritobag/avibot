import os
from dataclasses import dataclass


@dataclass
class Bot:
    token: str = os.environ.get("BOT_TOKEN", "")
    complaint_email: str = os.environ.get("COMPLAINT_EMAIL", "")
    preload_ext = ["commands", "complaint", "nsa", "youtube"]
    prefix = "!"
    debug: bool = bool(os.environ.get("AVIBOT_DEBUG", ""))


@dataclass
class Database:
    hostname: str = os.environ.get("POSTGRES_HOST", "")
    username: str = os.environ.get("POSTGRES_USER", "")
    password: str = os.environ.get("POSTGRES_PASSWORD", "")
    database: str = os.environ.get("POSTGRES_DB", "")


@dataclass
class Config:
    bot: Bot = Bot()
    database: Database = Database()
