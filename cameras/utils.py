from datetime import datetime, timedelta

import numpy as np

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
    ServiceMessageORM,
    ParkingLotORM
    )


async def is_user(plate: str, db: AsyncSession) -> bool:
    """Check if a car with the given license plate exists in the database.

        Args:
            plate (str): The license plate of the car.
            db (AsyncSession): The database session to execute the query.

        Returns:
            bool: True if the car exists, False otherwise.
        """

    stmnt = select(CarORM).where(CarORM.car_plate == plate)
    res = await db.execute(stmnt)
    car = res.scalar_one_or_none()

    if car:
        return True
    return False


async def is_banned(plate: str, db: AsyncSession) -> bool:
    """Check if the owner of a car with the given license plate is banned.

        Args:
            plate (str): The license plate of the car.
            db (AsyncSession): The database session to execute the query.

        Returns:
            bool: True if the owner is banned, False otherwise.
        """

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
    """Check if the owner of a car with the given license plate is an admin and can be credited.

        Args:
            plate (str): The license plate of the car.
            db (AsyncSession): The database session to execute the query.

        Returns:
            bool: True if the owner is an admin and can be credited, False otherwise.
        """

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
    """Fetches the tariff for a specific date.

        This function retrieves the tariff from the `TariffORM` table that was
        set on or before the specified date. It orders the tariffs by `set_date`
        in descending order to get the latest tariff up to that date.

        Args:
            date (datetime.date): The date to find the tariff for.
            db (AsyncSession): The asynchronous database session.

        Returns:
            float: The tariff value for the specified date.
        """
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
    """Fetches the credit limit for a specific date.

        This function retrieves the credit limit from the `CreditLimitsORM` table
        that was set on or before the specified date. It orders the limits by `set_date`
        in descending order to get the latest limit up to that date.

        Args:
            date (datetime.date): The date to find the credit limit for.
            db (AsyncSession): The asynchronous database session.

        Returns:
            float: The credit limit for the specified date.
        """
    stmnt = (
        select(CreditLimitsORM)
        .where(CreditLimitsORM.set_date <= date)
        .order_by(CreditLimitsORM.set_date.desc())
        )
    res = await db.execute(stmnt)
    limit = res.scalars().first()

    return limit.limit


async def set_unleaved_ban(car: CarORM, db: AsyncSession) -> int:
    """Sets a ban for a car that has not left the parking area.

        This function marks the end time of a parking session for the specified car
        if no end time is currently set (i.e., the car has not left). It calculates
        the parking cost based on the tariff applicable at the start time and
        marks the bill as sent and the user as banned. The user's account is
        updated accordingly.

        Args:
            car (CarORM): The car object representing the vehicle to be banned.
            db (AsyncSession): The asynchronous database session.

        Returns:
            int: The bill ID of the updated parking session.
        """
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

    cost = round(tariff * time_diff_minutes, 2)
    parking_db.bill.cost = cost
    parking_db.bill.is_sent = True
    parking_db.bill.is_ban = True

    parking_db.car.owner.is_banned = True
    await db.commit()

    return parking_db.bill.id


async def set_unparked_ban(car: CarORM, db: AsyncSession) -> int:
    """
        Imposes a ban on a car if it has unpaid bills for more than 30 days, applies a fine, and updates the car's ban status.

        Args:
            car (CarORM): The car object for which the ban is being applied.
            db (AsyncSession): The database session used for querying and updating records.

        Returns:
            int: The ID of the bill generated for the fine.
        """
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
        fine = round(fine, 2) if fine >= 150 else 150
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
    """
        Sends a ban notification to the user with a specific bill ID.

        Args:
            user_id (int): The ID of the user to whom the message is being sent.
            bill_id (int): The ID of the bill associated with the ban.
            ban_message (str): The message content to be sent, with details about the ban.
            db (AsyncSession): The database session used for querying and updating records.

        Returns:
            int: The ID of the generated message.
        """
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


async def send_message(user_id: int,
                       bill_id: int,
                       db: AsyncSession) -> int:
    """
        Sends a message to the user regarding the payment of a specific bill.

        Args:
            user_id (int): The ID of the user to whom the message is being sent.
            bill_id (int): The ID of the bill associated with the message.
            db (AsyncSession): The database session used for querying and updating records.

        Returns:
            int: The ID of the generated message.
        """
    stmnt = (
        select(BillingORM)
        .where(BillingORM.id == bill_id)
        .options(
            selectinload(BillingORM.history),
            selectinload(BillingORM.history).selectinload(ParkingHistoryORM.car)
        )
        )
    res = await db.execute(stmnt)
    bill = res.scalar_one()

    start_date = bill.history.start_time.strftime('%Y-%m-%d')

    message = (f" Сплатіть рахунок № {bill.id} на суму {bill.cost}"
               + f" за паркування автомобіля {bill.history.car.car_plate}"
               + f" початок {start_date}."
               )

    message = ServiceMessageORM(
        message=message,
        user_id=user_id,
        bill_id=bill.id,
        is_ban=False
    )

    db.add(message)
    await db.commit()

    return message.id


async def occupy_lot(
        car_id: int,
        db: AsyncSession
) -> None:
    """
        Occupies a free parking lot with a specific car ID.

        Args:
            car_id (int): The ID of the car that will occupy the lot.
            db (AsyncSession): The database session used for querying and updating records.

        Returns:
            None
        """
    stmnt = select(ParkingLotORM).where(ParkingLotORM.car_id.is_(None))
    res = await db.execute(stmnt)
    free_lots = res.scalars().all()

    ids = tuple(lot.id for lot in free_lots)
    occupied = np.random.choice(ids)

    stmnt = select(ParkingLotORM).where(ParkingLotORM.id == occupied)
    res = await db.execute(stmnt)
    lot = res.scalar_one_or_none()
    lot.car_id = car_id

    await db.commit()
    return


async def free_lot(
        car_id: int,
        db: AsyncSession
) -> None:
    """
        Frees a parking lot by removing the associated car ID.

        Args:
            car_id (int): The ID of the car currently occupying the lot.
            db (AsyncSession): The database session used for querying and updating records.

        Returns:
            None
        """
    stmnt = select(ParkingLotORM).where(ParkingLotORM.car_id == car_id)
    res = await db.execute(stmnt)
    lot = res.scalar()

    if lot is None:
        return
    
    lot.car_id = None
    
    await db.commit()
    return
