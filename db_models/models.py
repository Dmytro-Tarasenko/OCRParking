from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float, DateTime
from sqlalchemy.orm import relationship
from db import Base
from datetime import datetime


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)
    cars = relationship('Car', back_populates='owner')


class Car(Base):
    __tablename__ = 'cars'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    car_plate = Column(String, nullable=False)
    owner = relationship('User', back_populates='cars')
    parking_history = relationship('ParkingHistory', back_populates='car')


class ParkingHistory(Base):
    __tablename__ = 'parking_history'

    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    car_id = Column(Integer, ForeignKey('cars.id'), nullable=False)
    parking_cost = Column(Float)
    bill_id = Column(Integer, ForeignKey('billing.id'))
    car = relationship('Car', back_populates='parking_history')




class Billing(Base):
    __tablename__ = 'billing'

    id = Column(Integer, primary_key=True, index=True)
    parking_history_id = Column(Integer, ForeignKey('parking_history.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    cost = Column(Float, nullable=False)
    is_sent = Column(Boolean, default=False)
    is_paid = Column(Boolean, default=False)
