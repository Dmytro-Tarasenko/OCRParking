from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float, DateTime
from sqlalchemy.orm import relationship
from db_models.db import Base
from datetime import datetime


class User(Base):
    """
        Represents a user in the system.

        Attributes:
            id (int): Unique identifier for the user.
            username (str): Unique username for the user.
            email (str): Unique email address of the user.
            password (str): Hashed password of the user.
            is_admin (bool): Flag indicating if the user is an admin. Default is False.
            is_banned (bool): Flag indicating if the user is banned. Default is False.
            cars (list of Car): List of cars owned by the user. Related via a one-to-many relationship.
        """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)
    cars = relationship('Car', back_populates='owner')


class Car(Base):
    """
        Represents a car in the system.

        Attributes:
            id (int): Unique identifier for the car.
            user_id (int): Foreign key referencing the user who owns the car.
            car_plate (str): License plate of the car.
            owner (User): The user who owns the car.
            parking_history (list of ParkingHistory): List of parking history records related to the car.
        """
    __tablename__ = 'cars'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    car_plate = Column(String, nullable=False)
    owner = relationship('User', back_populates='cars')
    parking_history = relationship('ParkingHistory', back_populates='car')


class ParkingHistory(Base):
    """
        Represents the parking history of a car.

        Attributes:
            id (int): Unique identifier for the parking record.
            start_time (datetime): The time when parking started. Defaults to current UTC time.
            end_time (datetime): The time when parking ended.
            car_id (int): Foreign key referencing the car involved in the parking event.
            parking_cost (float): The cost of parking for the duration.
            bill_id (int): Foreign key referencing the billing record.
            car (Car): The car related to this parking history entry.
        """
    __tablename__ = 'parking_history'

    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    car_id = Column(Integer, ForeignKey('cars.id'), nullable=False)
    parking_cost = Column(Float)
    bill_id = Column(Integer, ForeignKey('billing.id'))
    car = relationship('Car', back_populates='parking_history')


class Billing(Base):
    """
        Represents a billing record for parking.

        Attributes:
            id (int): Unique identifier for the billing record.
            parking_history_id (int): Foreign key referencing the related parking history.
            user_id (int): Foreign key referencing the user being billed.
            cost (float): The amount billed.
            is_sent (bool): Flag indicating whether the bill has been sent to the user. Default is False.
            is_paid (bool): Flag indicating whether the bill has been paid. Default is False.
        """
    __tablename__ = 'billing'

    id = Column(Integer, primary_key=True, index=True)
    parking_history_id = Column(Integer, ForeignKey('parking_history.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    cost = Column(Float, nullable=False)
    is_sent = Column(Boolean, default=False)
    is_paid = Column(Boolean, default=False)
