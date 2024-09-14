from datetime import datetime, timedelta

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
    parking_db.bill.is_ban = True

    parking_db.car.owner.is_banned = True
    await db.commit()

    return parking_db.bill.id


async def set_unparked_ban(car: CarORM, db: AsyncSession) -> int:
    date_limit = datetime.today().date() - timedelta(days=30)
    end_time = datetime.now() - timedelta(minutes=59)
    start_time = end_time - timedelta(hours=1)
    stmnt = (
        select(BillingORM)
        .join(ParkingHistoryORM)
        .where(
            ParkingHistoryORM.car_id == car.id,
            ParkingHistoryORM.end_time > date_limit
            )
    )
    res = await db.execute(stmnt)
    bills_db = res.scalars().all()

    if len(bills_db) > 0:
        fine = max([bill.cost for bill in bills_db])
        fine = fine if fine >= 150 else 150
    else:
        fine = 150

    parking_fine = ParkingHistoryORM(
        start_time=start_time,
        end_time=end_time
    )
    parking_fine.car = car
    bill_fine = BillingORM(
        user_id=car.owner.id,
        cost=fine,
        is_sent=True,
        is_ban=True
    )
    parking_fine.bill = bill_fine
    parking_fine.car.owner.is_banned = True

    db.add(parking_fine)
    await db.commit()

    parking_current = ParkingHistoryORM(
        start_time=end_time + timedelta(minutes=1)
    )
    bill_new = BillingORM(
        user_id=car.owner.id
    )
    parking_current.bill = bill_new
    parking_current.car = car

    db.add(parking_current)
    await db.commit()

    return bill_fine.id


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
        bill_id=bill.id,
        is_ban=True
    )

    db.add(message)
    await db.commit()

    return message.id
