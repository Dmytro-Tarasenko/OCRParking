from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from db_models.db import get_session
from db_models.orms import CarORM, BillingORM, ParkingHistoryORM


async def is_user(plate: str, db: AsyncSession) -> bool:

    stmnt = select(CarORM).where(CarORM.car_plate == plate)
    res = await db.execute(stmnt)
    car = res.scalar_one_or_none()

    if car:
        return True
    return False


async def is_banned(plate: str, db: AsyncSession) -> bool:

    stmnt = (
        select(CarORM).filter(CarORM.car_plate == plate)
        .options(selectinload(CarORM.owner))
    )
    res = await db.execute(stmnt)
    car = res.scalar_one_or_none()

    if car.owner.is_banned:
        return True
    return False


async def is_creditable(plate: str, db: AsyncSession) -> bool:

    async with get_session() as session:
        stmnt = select(Car).filter(Car.car_plate == plate) \
            .options(selectinload(Car.owner))
        res = await session.execute(stmnt)
        car = res.scalars().first()

        if car.owner.is_admin:
            return True
    return False


async def is_parked(plate: str, db: AsyncSession) -> bool:

    return False


async def is_out(plate: str, db: AsyncSession) -> bool:

    return False