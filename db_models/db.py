from sqlalchemy.ext.asyncio import (AsyncSession,
                                    create_async_engine,
                                    AsyncAttrs)
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.ext.declarative import declarative_base
from settings import settings

DATABASE_URL = settings.database_url
if DATABASE_URL is None:
    raise ValueError("DATABASE_URL is not set in the environment variables")

engine = create_async_engine(DATABASE_URL, echo=True)

Base = declarative_base()


class BaseORM(AsyncAttrs, DeclarativeBase):
    pass


async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
