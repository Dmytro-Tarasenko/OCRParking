from typing import List, Optional

from sqlalchemy import String, Boolean, ForeignKey, Float, DateTime, Date, select, func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from db_models.db import BaseORM
from datetime import datetime


class UserORM(BaseORM):
    """
        ORM class for the 'users' table, representing a user in the system.

        Attributes:
            id (int): The primary key of the user.
            username (str): The unique username of the user.
            email (str): The unique email address of the user.
            password (str): The hashed password of the user.
            is_admin (bool): Whether the user is an administrator.
            is_banned (bool): Whether the user is banned.

        Relationships:
            cars (List[CarORM]): A list of cars owned by the user.
            bills (List[BillingORM]): A list of bills associated with the user.
            messages (List[ServiceMessageORM]): A list of service messages associated with the user.
        """
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
    messages: Mapped[List['ServiceMessageORM']] = relationship(
        'ServiceMessageORM',
        back_populates='user'
    )


class CarORM(BaseORM):
    """
        ORM class for the 'cars' table, representing a car in the system.

        Attributes:
            id (int): The primary key of the car.
            user_id (int): The foreign key referencing the owner of the car.
            car_plate (str): The license plate of the car.

        Relationships:
            owner (UserORM): The user who owns the car.
            parking_history (List[ParkingHistoryORM]): A list of parking history records for the car.
        """
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
    """
        ORM class for the 'parking_history' table, representing a record of parking.

        Attributes:
            id (int): The primary key of the parking history record.
            start_time (datetime): The start time of the parking.
            end_time (Optional[datetime]): The end time of the parking.
            car_id (int): The foreign key referencing the car.

        Relationships:
            car (CarORM): The car associated with the parking record.
            bill (BillingORM): The billing information for the parking session.
        """
    __tablename__ = 'parking_history'

    id: Mapped[int] = mapped_column(primary_key=True)
    start_time: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now()
        )
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime,
                                                         default=None)
    car_id: Mapped[int] = mapped_column(ForeignKey('cars.id'),
                                        nullable=False)

    # relations
    car: Mapped[CarORM] = relationship(CarORM,
                                       back_populates="parking_history")
    bill: Mapped["BillingORM"] = relationship("BillingORM",
                                              back_populates="history")


class BillingORM(BaseORM):
    """
        ORM class for the 'billing' table, representing a bill associated with a parking session.

        Attributes:
            id (int): The primary key of the bill.
            parking_history_id (int): The foreign key referencing the parking history.
            user_id (int): The foreign key referencing the user associated with the bill.
            cost (Optional[float]): The cost of the parking session.
            is_sent (bool): Whether the bill has been sent to the user.
            is_paid (bool): Whether the bill has been paid.

        Relationships:
            history (ParkingHistoryORM): The parking history associated with the bill.
            user (UserORM): The user associated with the bill.
            message (ServiceMessageORM): A service message associated with the bill.
        """
    __tablename__ = 'billing'

    id: Mapped[int] = mapped_column(primary_key=True)
    parking_history_id: Mapped[int] = mapped_column(
        ForeignKey('parking_history.id', ondelete='CASCADE')
        )
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id',
                                                    ondelete='CASCADE'))
    cost: Mapped[Optional[float]] = mapped_column(Float, default=None)
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    is_ban: Mapped[Optional[bool]] = mapped_column(Boolean,
                                                   nullable=True,
                                                   default=False)

    # relations
    history: Mapped[ParkingHistoryORM] = relationship(
        ParkingHistoryORM,
        back_populates="bill",
        foreign_keys=[parking_history_id]
        )
    user: Mapped[UserORM] = relationship(UserORM, back_populates="bills")
    message: Mapped["ServiceMessageORM"] = relationship(
        "ServiceMessageORM",
        back_populates='bill'
    )


class ServiceMessageORM(BaseORM):
    """
        ORM class for the 'messages' table, representing a service message for a user or bill.

        Attributes:
            id (int): The primary key of the message.
            user_id (int): The foreign key referencing the user.
            bill_id (Optional[int]): The foreign key referencing the bill, if applicable.
            message (str): The content of the service message.
            is_active (bool): Whether the message is currently active.

        Relationships:
            user (UserORM): The user associated with the message.
            bill (BillingORM): The bill associated with the message, if applicable.
        """
    __tablename__ = 'messages'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id',
                                                    ondelete='CASCADE'))
    bill_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('billing.id',
                   ondelete='CASCADE')
        )
    message: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_ban: Mapped[Optional[bool]] = mapped_column(Boolean,
                                                   nullable=True,
                                                   default=False)

    # relations
    user: Mapped[UserORM] = relationship(UserORM, back_populates='messages')
    bill: Mapped[BillingORM] = relationship(BillingORM,
                                            back_populates='message',
                                            foreign_keys=[bill_id]
                                            )


class TariffORM(BaseORM):
    """
        ORM class for the 'tariffs' table, representing the parking tariffs.

        Attributes:
            id (int): The primary key of the tariff record.
            tariff (float): The tariff rate.
            set_date (date): The date the tariff was set.
        """
    __tablename__ = "tariffs"

    id: Mapped[int] = mapped_column(primary_key=True)
    tariff: Mapped[float] = mapped_column(Float)
    set_date: Mapped[Date] = mapped_column(Date,
                                           default=datetime.today().date())


class CreditLimitsORM(BaseORM):
    """
        ORM class for the 'credit_limits' table, representing user credit limits.

        Attributes:
            id (int): The primary key of the credit limit record.
            limit (float): The credit limit amount.
            set_date (date): The date the credit limit was set.
        """
    __tablename__ = "credit_limits"

    id: Mapped[int] = mapped_column(primary_key=True)
    limit: Mapped[float] = mapped_column(Float)
    set_date: Mapped[Date] = mapped_column(Date,
                                           default=datetime.today().date())


class ParkingLotORM(BaseORM):
    __tablename__ = 'parking_lots'

    id: Mapped[int] = mapped_column(primary_key=True)
    car_id: Mapped[int] = mapped_column(ForeignKey('cars.id'), nullable=True)

    # #relations
    # car: Mapped[CarORM] = relationship(CarORM)
