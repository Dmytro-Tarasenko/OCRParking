from sqlalchemy import select
from sqlalchemy.orm import selectinload

from db_models.db import get_session
from db_models.models import Car, User, Billing, ParkingHistory

async def is_user(plate: str) -> bool:

    async with get_session() as session:
        stmnt = select(Car).filter(Car.car_plate == plate)
        res = await session.execute(stmnt)
        car = res.scalars().first()

        if car:
            return True
    return False


async def is_banned(plate: str) -> bool:

    async with get_session() as session:
        stmnt = select(Car).filter(Car.car_plate == plate) \
            .options(selectinload(Car.owner))
        res = await session.execute(stmnt)
        car = res.scalars().first()

        if car.owner.is_banned:
            return True
    return False


async def is_creditable(pate: str) -> bool:

    async with get_session() as session:
        stmnt = select(Car).filter(Car.car_plate == plate) \
            .options(selectinload(Car.owner))
        res = await session.execute(stmnt)
        car = res.scalars().first()

        if car.owner.is_admin:
            return True
    return False


async def is_parked(plate: str) -> bool:


    return False


async def is_out(plate: str) -> bool:


    return False