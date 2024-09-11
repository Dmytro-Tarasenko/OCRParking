import json

from fastapi.responses import HTMLResponse

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from routes.auth import Authentication
from db_models.db import get_session
from schemas.auth import UserCreate
from db_models.models import User as UserModel, ParkingHistory, Billing
from db_models.models import Car

auth = Authentication()
import logging

logging.basicConfig(level=logging.DEBUG)

router = APIRouter(prefix='/admin',
                   tags=["Admin"])


@router.get('/')
def get_user_page(request):
    pass


@router.post("/add_user", dependencies=[Depends(auth.oauth2_scheme)], status_code=status.HTTP_201_CREATED)
async def add_user(user: UserCreate, db: AsyncSession = Depends(get_session)):
    existing_user = await db.execute(select(UserModel).where(UserModel.username == user.username))
    if existing_user.scalar():
        return {"error": "Username already registered"}

    hashed_password = auth.get_password_hash(user.password)
    new_user = UserModel(username=user.username, email=user.email, password=hashed_password)

    db.add(new_user)
    await db.commit()
    return {"msg": "User added successfully"}


@router.delete("/delete_user/{username}", dependencies=[Depends(auth.oauth2_scheme)], status_code=200)
async def delete_user(username: str, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(UserModel).where(UserModel.username == username))
    user = result.scalar()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(user)
    await db.commit()
    return {"msg": "User deleted successfully"}


@router.put("/toggle_ban/{username}", dependencies=[Depends(auth.oauth2_scheme)])
async def toggle_user_ban(username: str, db: AsyncSession = Depends(get_session)):
    user = await db.execute(select(UserModel).where(UserModel.username == username))
    user = user.scalar()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_banned = not user.is_banned
    await db.commit()
    return {"msg": f"User {'banned' if user.is_banned else 'unbanned'} successfully"}


# @router.put("/set_parking_tariff", dependencies=[Depends(auth.oauth2_scheme)])
# async def set_parking_tariff(new_rate: float, db: AsyncSession = Depends(get_session),
#                              admin: UserModel = Depends(auth.admin_required)):
#     if not admin.is_admin:
#         raise HTTPException(status_code=403, detail="Not enough privileges")
#
#     return {"msg": f"Parking tariff set to {new_rate} successfully"}


@router.get("/user_stats/{username}", dependencies=[Depends(auth.oauth2_scheme)])
async def get_user_stats(username: str, db: AsyncSession = Depends(get_session)):
    user = await db.execute(select(UserModel).where(UserModel.username == username))
    user = user.scalar()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    parking_history = await db.execute(select(ParkingHistory).where(ParkingHistory.car_id.in_(
        select(Car.id).where(Car.user_id == user.id)
    )))
    history = parking_history.scalars().all()

    return {
        "username": user.username,
        "email": user.email,
        "cars": [car.car_plate for car in user.cars],
        "parking_history": [
            {
                "start_time": record.start_time,
                "end_time": record.end_time,
                "cost": record.parking_cost
            }
            for record in history
        ]
    }


@router.get("/car_stats/{car_id}", dependencies=[Depends(auth.oauth2_scheme)])
async def get_car_stats(car_id: int, db: AsyncSession = Depends(get_session)):
    car = await db.get(Car, car_id)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    parking_history = await db.execute(select(ParkingHistory).where(ParkingHistory.car_id == car_id))
    history = parking_history.scalars().all()

    return {
        "car_plate": car.car_plate,
        "parking_history": [
            {
                "start_time": record.start_time,
                "end_time": record.end_time,
                "cost": record.parking_cost
            }
            for record in history
        ]
    }


@router.get("/parking_stats", dependencies=[Depends(auth.oauth2_scheme)])
async def get_parking_stats(db: AsyncSession = Depends(get_session)):
    total_parkings = await db.execute(select(ParkingHistory))
    total_cost = await db.execute(select(Billing.cost))

    total_parkings_count = total_parkings.scalars().count()
    total_earned = sum(bill.cost for bill in total_cost.scalars())

    return {
        "total_parkings": total_parkings_count,
        "total_earned": total_earned
    }
