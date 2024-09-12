import asyncio
from db import engine, BaseORM
from orms import UserORM, CarORM, ParkingHistoryORM, BillingORM


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(BaseORM.metadata.create_all)


if __name__ == "__main__":
    asyncio.run(init_db())
