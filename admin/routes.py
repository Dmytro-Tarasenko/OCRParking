from datetime import timedelta, datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from db_models.settings import Settings
from routes.auth import Authentication
from db_models.db import get_session
from schemas.auth import UserCreate
from db_models.models import User as UserModel, ParkingHistory, Billing, User
from db_models.models import Car

auth = Authentication()
settings = Settings()
router = APIRouter(prefix='/admin',
                   default_response_class=HTMLResponse,
                   include_in_schema=False,
                   tags=["Admin"])


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
        return {"error": "User not found", "status_code": 404}

    await db.delete(user)
    await db.commit()
    return {"msg": "User deleted successfully"}


@router.put("/toggle_ban/{username}", dependencies=[Depends(auth.oauth2_scheme)])
async def toggle_user_ban(username: str, db: AsyncSession = Depends(get_session)):
    user = await db.execute(select(UserModel).where(UserModel.username == username))
    user = user.scalar()
    if not user:
        return {"error": "User not found"}

    user.is_banned = not user.is_banned
    await db.commit()
    return {"msg": f"User {'banned' if user.is_banned else 'unbanned'} successfully"}


# @router.put("/set_parking_tariff", dependencies=[Depends(auth.oauth2_scheme)])
# async def set_parking_tariff(new_rate: float, db: AsyncSession = Depends(get_session),
#                              admin: UserModel = Depends(auth.admin_required)):
#     if not admin.is_admin:
#         return {"error": "Not enough privileges", "status_code": 403}
#
#     # Логіка встановлення тарифу
#     return {"msg": f"Parking tariff set to {new_rate} successfully"}


@router.get("/user_stats/{username}", dependencies=[Depends(auth.oauth2_scheme)])
async def get_user_stats(username: str, db: AsyncSession = Depends(get_session)):
    user = await db.execute(select(UserModel).where(UserModel.username == username))
    user = user.scalar()
    if not user:
        return {"error": "User not found"}

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
        return {"error": "Car not found", "status_code": 404}

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
    try:
        total_parkings = await db.execute(select(ParkingHistory))
        total_cost = await db.execute(select(Billing.cost))

        total_parkings_count = total_parkings.scalars().count()
        total_earned = sum(bill.cost for bill in total_cost.scalars())

        return {
            "total_parkings": total_parkings_count,
            "total_earned": total_earned
        }
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}", "status_code": 500}


@router.get("/active_users_stats", dependencies=[Depends(auth.oauth2_scheme)])
async def get_active_users_stats(db: AsyncSession = Depends(get_session)):
    last_month = datetime.now() - timedelta(days=30)
    active_users = await db.execute(
        select(func.count(User.id)).join(ParkingHistory).where(ParkingHistory.start_time >= last_month)
    )
    count_active_users = active_users.scalar()

    return {"active_users_count": count_active_users}


@router.get("/banned_users_stats", dependencies=[Depends(auth.oauth2_scheme)])
async def get_banned_users_stats(db: AsyncSession = Depends(get_session)):
    banned_users = await db.execute(
        select(func.count(User.id)).where(User.is_banned == True)
    )
    count_banned_users = banned_users.scalar()

    return {"banned_users_count": count_banned_users}


@router.get("/parking_occupancy_stats", dependencies=[Depends(auth.oauth2_scheme)])
async def get_parking_occupancy_stats(db: AsyncSession = Depends(get_session), period: str = "day"):
    now = datetime.now()

    if period == "week":
        start_time = now - timedelta(weeks=1)
    elif period == "month":
        start_time = now - timedelta(days=30)
    else:
        start_time = now - timedelta(days=1)

    total_parkings = await db.execute(
        select(func.count(ParkingHistory.id)).where(ParkingHistory.start_time >= start_time)
    )
    total_parkings_count = total_parkings.scalar()

    average_occupancy = (total_parkings_count / (settings.TOTAL_SPOTS * 24)) * 100

    return {"average_occupancy_percent": average_occupancy}


@router.get("/max_cars_day_stats", dependencies=[Depends(auth.oauth2_scheme)])
async def get_max_cars_per_day_stats(db: AsyncSession = Depends(get_session)):
    max_cars = await db.execute(
        select(func.count(ParkingHistory.id)).group_by(func.date(ParkingHistory.start_time))
    )
    max_cars_per_day = max_cars.scalar()

    return {"max_cars_in_a_day": max_cars_per_day}


@router.get("/peak_activity_time_stats", dependencies=[Depends(auth.oauth2_scheme)])
async def get_peak_activity_time_stats(db: AsyncSession = Depends(get_session)):
    peak_time = await db.execute(
        select(func.extract('hour', ParkingHistory.start_time), func.count(ParkingHistory.id))
        .group_by(func.extract('hour', ParkingHistory.start_time))
        .order_by(func.count(ParkingHistory.id).desc())
    )
    most_active_hour, count = peak_time.first()

    return {"most_active_hour": most_active_hour, "parking_count": count}


@router.get("/average_parking_duration_stats", dependencies=[Depends(auth.oauth2_scheme)])
async def get_average_parking_duration_stats(db: AsyncSession = Depends(get_session)):
    average_duration = await db.execute(
        select(func.avg(func.extract('epoch', ParkingHistory.end_time - ParkingHistory.start_time)))
        .where(ParkingHistory.end_time.isnot(None))
    )
    average_duration_seconds = average_duration.scalar()

    average_duration_hours = average_duration_seconds / 3600 if average_duration_seconds else 0

    return {"average_parking_duration_hours": average_duration_hours}


@router.get("/parking_count_stats", dependencies=[Depends(auth.oauth2_scheme)])
async def get_parking_count_stats(db: AsyncSession = Depends(get_session), period: str = "day"):
    now = datetime.now()

    if period == "week":
        start_time = now - timedelta(weeks=1)
    elif period == "month":
        start_time = now - timedelta(days=30)
    else:
        start_time = now - timedelta(days=1)

    parking_count = await db.execute(
        select(func.count(ParkingHistory.id)).where(ParkingHistory.start_time >= start_time)
    )
    count = parking_count.scalar()

    return {"parking_count": count, "period": period}


@router.get("/available_spots_stats", dependencies=[Depends(auth.oauth2_scheme)])
async def get_available_spots_stats(db: AsyncSession = Depends(get_session)):
    occupied_spots = await db.execute(
        select(func.count(ParkingHistory.id)).where(ParkingHistory.end_time.is_(None))
    )
    occupied_spots_count = occupied_spots.scalar()

    available_spots = settings.TOTAL_SPOTS - occupied_spots_count

    return {"available_spots": available_spots}


@router.get("/average_car_parking_duration_stats", dependencies=[Depends(auth.oauth2_scheme)])
async def get_average_car_parking_duration_stats(db: AsyncSession = Depends(get_session)):
    average_duration = await db.execute(
        select(func.avg(func.extract('epoch', ParkingHistory.end_time - ParkingHistory.start_time)))
        .where(ParkingHistory.end_time.isnot(None))
    )
    average_duration_seconds = average_duration.scalar()

    average_duration_hours = average_duration_seconds / 3600 if average_duration_seconds else 0

    return {"average_car_parking_duration_hours": average_duration_hours}


# @router.get("/count_new_users_stats", dependencies=[Depends(auth.oauth2_scheme)])
# async def count_new_users_stats(db: AsyncSession = Depends(get_session), period: str = "day"):
#     now = datetime.now()
#
#     if period == "week":
#         start_time = now - timedelta(weeks=1)
#     elif period == "month":
#         start_time = now - timedelta(days=30)
#     else:
#         start_time = now - timedelta(days=1)
#
#     new_users = await db.execute(
#         select(func.count(User.id)).where(User.created_at >= start_time)
#     )
#     new_users_count = new_users.scalar()
#
#     return {"new_users_count": new_users_count, "period": period}
