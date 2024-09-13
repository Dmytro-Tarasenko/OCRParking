from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from db_models.db import get_session
from db_models.orms import (
    CarORM,
    BillingORM,
    ParkingHistoryORM,
    TariffORM,
    CreditLimitsORM,
    ServiceMessageORM
    )


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
        stmnt = select(CarORM).filter(CarORM.car_plate == plate) \
            .options(selectinload(CarORM.owner))
        res = await session.execute(stmnt)
        car = res.scalars().first()

        if car.owner.is_admin:
            return True
    return False


async def get_tariff_for_date(date: datetime.date,
                              db: AsyncSession) -> float:
    stmnt = (
        select(TariffORM)
        .where(TariffORM.set_date <= date)
        .order_by(TariffORM.set_date.desc())
        )
    res = await db.execute(stmnt)
    tariff = res.scalars().first()

    return tariff.tariff


async def get_credit_limit_for_date(date: datetime.date,
                                    db: AsyncSession) -> float:
    stmnt = (
        select(CreditLimitsORM)
        .where(CreditLimitsORM.set_date <= date)
        .order_by(CreditLimitsORM.set_date.desc())
        )
    res = await db.execute(stmnt)
    limit = res.scalars().first()

    return limit.limit


async def set_unleaved_ban(car: CarORM, db: AsyncSession) -> int:
    stmnt = (
        select(ParkingHistoryORM)
        .where(
            ParkingHistoryORM.car_id == car.id,
            ParkingHistoryORM.end_time.is_(None)
            )
        .options(
            selectinload(ParkingHistoryORM.bill),
            selectinload(ParkingHistoryORM.car).selectinload(CarORM.owner)
        )
    )
    res = await db.execute(stmnt)
    parking_db = res.scalars().first()
    parking_db.end_time = datetime.now()

    start_date = parking_db.start_time.date()
    tariff = await get_tariff_for_date(start_date, db)
    time_diff_minutes = (
        (parking_db.end_time - parking_db.start_time).seconds // 60
    )

    cost = tariff * time_diff_minutes
    parking_db.bill.cost = cost
    parking_db.bill.is_sent = True

    parking_db.car.owner.is_banned = True
    await db.commit()

    return parking_db.bill.id


async def set_unparked_ban(user_id: CarORM, db: AsyncSession) -> int:
    bill_id = 1

    return bill_id


async def send_ban_message(user_id: int,
                           bill_id: int,
                           ban_message: str,
                           db: AsyncSession) -> int:
    stmnt = select(BillingORM).where(BillingORM.id == bill_id)
    res = await db.execute(stmnt)
    bill = res.scalar_one()

    ban_message += f" Сплатіть рахунок № {bill.id} на суму {bill.cost} для зняття заборони."

    message = ServiceMessageORM(
        message=ban_message,
        user_id=user_id,
        bill_id=bill.id
    )

    db.add(message)
    await db.commit()

    return message.id
