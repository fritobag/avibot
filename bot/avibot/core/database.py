from sqlalchemy import BigInteger, Boolean, Column, Integer, String, delete, or_, update
from sqlalchemy import func
from sqlalchemy.sql import text
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.future import select
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.types import ARRAY

Base = declarative_base()


def stringfy_statement(statement):
    return statement.compile(dialect=postgresql.dialect())


class DatabaseInterface:
    def __init__(
        self,
        password: str,
        hostname: str = "localhost",
        username: str = "postgres",
        database: str = "avibot",
        port: int = 5432,
    ):
        self.password = password
        self.hostname = hostname
        self.username = username
        self.database = database
        self.port = port
        self.engine = create_async_engine(self.dsn)

    @property
    def dsn(self):
        return "postgresql+asyncpg://{}:{}@{}:{}/{}".format(
            self.username, self.password, self.hostname, self.port, self.database
        )

    def get_session(self):
        return sessionmaker(
            self.engine,
            expire_on_commit=False,
            future=True,
            class_=AsyncSession,
        )()

    async def create_database(self):
        async with self.engine.begin() as conn:
            # await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
