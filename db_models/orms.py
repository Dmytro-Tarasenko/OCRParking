from typing import List, Optional

from sqlalchemy import String, Boolean, ForeignKey, Float, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from db_models.db import BaseORM
from datetime import datetime


class UserORM(BaseORM):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)

    # relations
    cars: Mapped[List["CarORM"]] = relationship(
        "CarORM",
        back_populates="owner"
        )
    bills: Mapped[List["BillingORM"]] = relationship(
        "BillingORM",
        back_populates="user"
        )


class CarORM(BaseORM):
    __tablename__ = 'cars'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'),
                                         nullable=False)
    car_plate: Mapped[str] = mapped_column(String, nullable=False)

    # relations
    owner: Mapped[UserORM] = relationship(UserORM, back_populates="cars")
    parking_history: Mapped[List["ParkingHistoryORM"]] = \
        relationship(
            "ParkingHistoryORM",
            back_populates="car"
        )


class ParkingHistoryORM(BaseORM):
    __tablename__ = 'parking_history'

    id: Mapped[int] = mapped_column(primary_key=True)
    start_time: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(datetime.UTC)
        )
    end_time: Mapped[datetime] = mapped_column(DateTime)
    car_id: Mapped[int] = mapped_column(ForeignKey('cars.id'), nullable=False)
    # parking_cost: Mapped[float] = mapped_column(Float)
    bill_id: Mapped[int] = mapped_column(ForeignKey('billing.id'))

    # relations
    car: Mapped[CarORM] = relationship(CarORM,
                                       back_populates="parking_history")
    bill: Mapped["BillingORM"] = relationship("BillingORM",
                                              back_populates="parking_history")


class BillingORM(BaseORM):
    __tablename__ = 'billing'

    id: Mapped[int] = mapped_column(primary_key=True)
    parking_history_id: Mapped[int] = mapped_column(
        ForeignKey('parking_history.id')
        )
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    cost: Mapped[Optional[float]] = mapped_column(Float, default=None)
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False)

    # relations
    parking_history: Mapped[ParkingHistoryORM] = relationship(
        ParkingHistoryORM,
        back_populates="bill"
        )
    user: Mapped[UserORM] = relationship(UserORM, back_populates="bills")
