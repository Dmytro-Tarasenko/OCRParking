from datetime import timedelta, datetime

from typing import Annotated, Any, Optional

from fastapi import APIRouter, Depends, Request, Cookie, Form
from fastapi.responses import HTMLResponse
from sqlalchemy import func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from settings import EnvSettings
from auth.auth import Authentication
from db_models.db import get_session
from schemas.auth import UserCreate, User
from db_models.orms import UserORM, ParkingHistoryORM, BillingORM, CarORM, TariffORM
from frontend.routes import templates

auth = Authentication()
settings = EnvSettings()

router = APIRouter(prefix='/admin',
                   default_response_class=HTMLResponse,
                   # include_in_schema=False,
                   tags=["Admin"])


@router.get("/", response_class=HTMLResponse)
async def get_admin_page(
        request: Request,
        db: AsyncSession = Depends(get_session),
        access_token: Annotated[str | None, Cookie()] = None
):
    if not access_token:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    current_username = auth.get_current_user(request)

    result = await db.execute(select(UserORM).where(UserORM.username == current_username))
    user_db = result.scalar()

    if not user_db or not user_db.is_admin:
        return templates.TemplateResponse("admin/mistake.html", {"request": request, "message": "Access denied. "
                                                                                                "Admins only."})

    return templates.TemplateResponse("admin/admin.html", {"request": request, "user": user_db})


@router.get("/user_management", response_class=HTMLResponse, name="get_user_management")
async def get_user_management(request: Request, db: AsyncSession = Depends(get_session),
                              access_token: Annotated[str | None, Cookie()] = None):
    if not access_token:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    current_username = auth.get_current_user(request)
    res = await db.execute(select(UserORM).where(UserORM.username == current_username))
    current_user = res.scalar()

    if not current_user or not current_user.is_admin:
        return templates.TemplateResponse('auth/login_form.html',
                                          {'request': request, 'user': None, 'error': 'Admin access required'})

    return templates.TemplateResponse("admin/user_management.html", {"request": request})


@router.get("/tariff_management", response_class=HTMLResponse, name="get_tariff_management")
async def get_tariff_management(request: Request, db: AsyncSession = Depends(get_session),
                                access_token: Annotated[str | None, Cookie()] = None):
    if not access_token:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    current_username = auth.get_current_user(request)
    res = await db.execute(select(UserORM).where(UserORM.username == current_username))
    current_user = res.scalar()

    if not current_user or not current_user.is_admin:
        return templates.TemplateResponse('auth/login_form.html',
                                          {'request': request, 'user': None, 'error': 'Admin access required'})

    return templates.TemplateResponse("admin/tariff_management.html", {"request": request})


@router.get("/blacklist_management", response_class=HTMLResponse, name="get_blacklist_management")
async def get_blacklist_management(request: Request, access_token: Annotated[str | None, Cookie()] = None,
                                   db: AsyncSession = Depends(get_session)):
    if not access_token:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    current_username = auth.get_current_user(request)
    res = await db.execute(select(UserORM).where(UserORM.username == current_username))
    current_user = res.scalar()

    if not current_user or not current_user.is_admin:
        return templates.TemplateResponse('auth/login_form.html',
                                          {'request': request, 'user': None, 'error': 'Admin access required'})

    return templates.TemplateResponse("admin/blacklist_management.html", {"request": request, "user": current_user})


@router.get("/user_list", response_class=HTMLResponse, name="get_user_list")
async def get_user_list(request: Request, db: AsyncSession = Depends(get_session),
                        access_token: Annotated[str | None, Cookie()] = None):
    if not access_token:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    users = await db.execute(select(UserORM))
    user_list = users.scalars().all()

    return templates.TemplateResponse("admin/user_list.html", {"request": request, "users": user_list})


@router.get("/add_user", response_class=HTMLResponse)
async def add_user_form(request: Request, db: AsyncSession = Depends(get_session),
                        access_token: Annotated[str | None, Cookie()] = None):
    if not access_token:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    current_username = auth.get_current_user(request)
    res = await db.execute(select(UserORM).where(UserORM.username == current_username))
    current_user = res.scalar()

    if not current_user or not current_user.is_admin:
        return templates.TemplateResponse('auth/login_form.html',
                                          {'request': request, 'user': None, 'error': 'Admin access required'})

    return templates.TemplateResponse("admin/add_user_form.html", {"request": request})


@router.post("/add_user", response_class=HTMLResponse)
async def add_user(
        request: Request,
        username: str = Form(...),
        email: str = Form(...),
        password: str = Form(...),
        db: AsyncSession = Depends(get_session),
        access_token: Annotated[str | None, Cookie()] = None
):
    if not access_token:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    current_username = auth.get_current_user(request)

    res = await db.execute(select(UserORM).where(UserORM.username == current_username))
    current_user = res.scalar()

    if not current_user or not current_user.is_admin:
        return templates.TemplateResponse('auth/login_form.html',
                                          {'request': request, 'error': 'Admin access required'})

    existing_user = await db.execute(select(UserORM).where(UserORM.username == username))
    if existing_user.scalar():
        return templates.TemplateResponse("admin/add_user_form.html", {
            "request": request,
            "error": "Username already registered."
        })

    hashed_password = auth.get_password_hash(password)
    new_user = UserORM(username=username, email=email, password=hashed_password)

    db.add(new_user)
    await db.commit()

    return templates.TemplateResponse("admin/user_added.html", {"request": request, "username": username})


@router.post("/delete_user", response_class=HTMLResponse)
async def delete_user(request: Request, username: str = Form(...), db: AsyncSession = Depends(get_session),
                      access_token: Annotated[str | None, Cookie()] = None):
    user = None
    if access_token:
        current_username = auth.get_current_user(request)
        user = await db.execute(select(UserORM).where(UserORM.username == current_username))
        user = user.scalar()

    if user is None or not user.is_admin:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': user})

    result = await db.execute(select(UserORM).where(UserORM.username == username))
    deleted_user = result.scalar()

    if not deleted_user:
        return templates.TemplateResponse("admin/delete_user_form.html", {
            "request": request,
            "error": "User not found."
        })

    await db.delete(deleted_user)
    await db.commit()

    return templates.TemplateResponse("admin/user_deleted.html", {"request": request, "username": username})


@router.get("/banned_users", response_class=HTMLResponse, name="get_banned_users")
async def get_banned_users(request: Request, db: AsyncSession = Depends(get_session),
                           access_token: Annotated[str | None, Cookie()] = None):
    user = None
    if access_token:
        username = auth.get_current_user(request)
        user = User(username=username)

    if user is None:
        return templates.TemplateResponse('auth/login_form.html',
                                          {'request': request,
                                           'user': user})

    users = await db.execute(select(UserORM).where(UserORM.is_banned == True))
    banned_users = users.scalars().all()

    return templates.TemplateResponse("admin/banned_users_list.html",
                                      {"request": request, "banned_users": banned_users})


from fastapi import HTTPException


@router.post("/ban_user", response_class=HTMLResponse)
async def ban_user(
        request: Request,
        username: str = Form(...),  # Отримання username через форму
        db: AsyncSession = Depends(get_session),
        access_token: Annotated[Optional[str], Cookie()] = None
):
    if not access_token:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    current_username = auth.get_current_user(request)

    res = await db.execute(select(UserORM).where(UserORM.username == current_username))
    current_user = res.scalar()

    if not current_user:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to ban users")

    res = await db.execute(select(UserORM).where(UserORM.username == username))
    banned_user = res.scalar()

    if not banned_user:
        raise HTTPException(status_code=404, detail="User not found")

    if banned_user.is_banned:
        return templates.TemplateResponse("admin/ban_user_form.html", {
            "request": request,
            "msg": f"User {banned_user.username} is already banned"
        })

    banned_user.is_banned = True
    await db.commit()

    return templates.TemplateResponse("admin/ban_success.html", {
        "request": request,
        "msg": f"User {banned_user.username} banned successfully"
    })


from fastapi import HTTPException


@router.post("/unban_user", response_class=HTMLResponse)
async def unban_user(
        request: Request,
        username: str = Form(...),
        db: AsyncSession = Depends(get_session),
        access_token: Annotated[Optional[str], Cookie()] = None
):
    if not access_token:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    current_username = auth.get_current_user(request)

    res = await db.execute(select(UserORM).where(UserORM.username == current_username))
    current_user = res.scalar()

    if not current_user:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to unban users")

    res = await db.execute(select(UserORM).where(UserORM.username == username))
    user = res.scalar()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.is_banned:
        return templates.TemplateResponse("admin/unban_user_form.html", {
            "request": request,
            "msg": f"User {user.username} is not banned"
        })

    user.is_banned = False
    await db.commit()

    return templates.TemplateResponse("admin/unban_success.html", {
        "request": request,
        "msg": f"User {user.username} unbanned successfully"
    })


@router.get("/tariffs", response_class=HTMLResponse)
async def list_tariffs(request: Request, db: AsyncSession = Depends(get_session),
                       access_token: Annotated[Optional[str], Cookie()] = None):
    if not access_token:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    current_username = auth.get_current_user(request)

    res = await db.execute(select(UserORM).where(UserORM.username == current_username))
    current_user = res.scalar()

    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to set parking tariff")

    result = await db.execute(select(TariffORM).order_by(TariffORM.set_date.desc()).limit(1))
    current_tariff = result.scalar()

    all_tariffs = await db.execute(select(TariffORM).order_by(TariffORM.set_date.desc()))
    tariffs = all_tariffs.scalars().all()

    return templates.TemplateResponse("admin/tariff_management.html", {
        "request": request,
        "current_tariff": current_tariff,
        "tariffs": tariffs
    })


@router.post("/tariffs/add", response_class=HTMLResponse)
async def add_tariff(
        request: Request,
        new_rate: float = Form(...),
        db: AsyncSession = Depends(get_session),
        access_token: Annotated[Optional[str], Cookie()] = None
):
    if not access_token:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    current_username = auth.get_current_user(request)

    res = await db.execute(select(UserORM).where(UserORM.username == current_username))
    current_user = res.scalar()

    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to set parking tariff")

    new_tariff = TariffORM(tariff=new_rate, set_date=datetime.today().date())

    db.add(new_tariff)
    await db.commit()

    return templates.TemplateResponse("admin/tariff_added.html", {
        "request": request,
        "msg": f"Parking tariff set to {new_rate} successfully"
    })


@router.get("/get_last_tariff", response_class=HTMLResponse)
async def get_last_tariff(request: Request, db: AsyncSession = Depends(get_session),
                          access_token: Annotated[Optional[str], Cookie()] = None):
    if not access_token:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    current_username = auth.get_current_user(request)

    res = await db.execute(select(UserORM).where(UserORM.username == current_username))
    current_user = res.scalar()

    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to set parking tariff")

    last_tariff = await db.execute(select(TariffORM).order_by(TariffORM.set_date.desc(), TariffORM.id.desc()).limit(1))
    tariff = last_tariff.scalar()
    if tariff:
        print(f"Тариф: {tariff.tariff}, Дата встановлення: {tariff.set_date}")
    else:
        print("Тариф не знайдено")

    return templates.TemplateResponse("admin/_last_tariff.html", {
        "request": request,
        "tariff": tariff
    })


@router.get("/user_stats", response_class=HTMLResponse)
async def get_user_stats(request: Request, username: str, db: AsyncSession = Depends(get_session),
                         access_token: Annotated[Optional[str], Cookie()] = None):
    if not access_token:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    current_username = auth.get_current_user(request)

    user = await db.execute(select(UserORM).where(UserORM.username == current_username))
    user = user.scalar()
    if not user:
        return {"error": "User not found"}

    parking_history = await db.execute(select(ParkingHistoryORM).where(ParkingHistoryORM.car_id.in_(
        select(CarORM.id).where(CarORM.user_id == user.id)
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
                "cost": record.bill
            }
            for record in history
        ]
    }


@router.get("/car_stats/{car_id}", response_class=HTMLResponse)
async def get_car_stats(request: Request, car_id: int, db: AsyncSession = Depends(get_session),
                        access_token: Annotated[Optional[str], Cookie()] = None):
    user = None
    if access_token:
        username = auth.get_current_user(request)
        user = User(username=username)

    if user is None:
        return templates.TemplateResponse('auth/login_form.html',
                                          {'request': request,
                                           'user': user})

    car = await db.get(CarORM, car_id)
    if not car:
        return {"error": "Car not found", "status_code": 404}

    parking_history = await db.execute(select(ParkingHistoryORM).where(ParkingHistoryORM.car_id == car_id))
    history = parking_history.scalars().all()

    return {
        "car_plate": car.car_plate,
        "parking_history": [
            {
                "start_time": record.start_time,
                "end_time": record.end_time,
                "cost": record.bill
            }
            for record in history
        ]
    }


@router.get("/parking_stats", response_class=HTMLResponse)
async def get_parking_stats(request: Request, access_token: Annotated[Optional[str], Cookie()] = None,
                            db: AsyncSession = Depends(get_session)):
    user = None
    if access_token:
        username = auth.get_current_user(request)
        user = User(username=username)

    if user is None:
        return templates.TemplateResponse('auth/login_form.html',
                                          {'request': request,
                                           'user': user})
    try:
        total_parkings = await db.execute(select(ParkingHistoryORM))
        total_cost = await db.execute(select(BillingORM.cost))

        total_parkings_count = total_parkings.scalars().count()
        total_earned = sum(bill.cost for bill in total_cost.scalars())

        return {
            "total_parkings": total_parkings_count,
            "total_earned": total_earned
        }
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}", "status_code": 500}


@router.get("/active_users_stats", response_class=HTMLResponse)
async def get_active_users_stats(request: Request, access_token: Annotated[Optional[str], Cookie()] = None,
                                 db: AsyncSession = Depends(get_session)):
    user = None
    if access_token:
        username = auth.get_current_user(request)
        user = User(username=username)

    if user is None:
        return templates.TemplateResponse('auth/login_form.html',
                                          {'request': request,
                                           'user': user})
    last_month = datetime.now() - timedelta(days=30)
    active_users = await db.execute(
        select(func.count(UserORM.id)).join(ParkingHistoryORM).where(ParkingHistoryORM.start_time >= last_month)
    )
    count_active_users = active_users.scalar()

    return {"active_users_count": count_active_users}


@router.get("/banned_users_stats", response_class=HTMLResponse)
async def get_banned_users_stats(request: Request, access_token: Annotated[Optional[str], Cookie()] = None,
                                 db: AsyncSession = Depends(get_session)):
    user = None
    if access_token:
        username = auth.get_current_user(request)
        user = User(username=username)

    if user is None:
        return templates.TemplateResponse('auth/login_form.html',
                                          {'request': request,
                                           'user': user})
    banned_users = await db.execute(
        select(func.count(UserORM.id)).where(UserORM.is_banned == True)
    )
    count_banned_users = banned_users.scalar()

    return {"banned_users_count": count_banned_users}


@router.get("/parking_occupancy_stats", response_class=HTMLResponse)
async def get_parking_occupancy_stats(request: Request, access_token: Annotated[Optional[str], Cookie()] = None,
                                      db: AsyncSession = Depends(get_session), period: str = "day"):
    user = None
    if access_token:
        username = auth.get_current_user(request)
        user = User(username=username)

    if user is None:
        return templates.TemplateResponse('auth/login_form.html',
                                          {'request': request,
                                           'user': user})
    now = datetime.now()

    if period == "week":
        start_time = now - timedelta(weeks=1)
    elif period == "month":
        start_time = now - timedelta(days=30)
    else:
        start_time = now - timedelta(days=1)

    total_parkings = await db.execute(
        select(func.count(ParkingHistoryORM.id)).where(ParkingHistoryORM.start_time >= start_time)
    )
    total_parkings_count = total_parkings.scalar()

    average_occupancy = (total_parkings_count / (settings.TOTAL_SPOTS * 24)) * 100

    return {"average_occupancy_percent": average_occupancy}


@router.get("/max_cars_day_stats", response_class=HTMLResponse)
async def get_max_cars_per_day_stats(request: Request, access_token: Annotated[Optional[str], Cookie()] = None,
                                     db: AsyncSession = Depends(get_session)):
    user = None
    if access_token:
        username = auth.get_current_user(request)
        user = User(username=username)

    if user is None:
        return templates.TemplateResponse('auth/login_form.html',
                                          {'request': request,
                                           'user': user})
    max_cars = await db.execute(
        select(func.count(ParkingHistoryORM.id)).group_by(func.date(ParkingHistoryORM.start_time))
    )
    max_cars_per_day = max_cars.scalar()

    return {"max_cars_in_a_day": max_cars_per_day}


@router.get("/peak_activity_time_stats", response_class=HTMLResponse)
async def get_peak_activity_time_stats(request: Request, access_token: Annotated[Optional[str], Cookie()] = None,
                                       db: AsyncSession = Depends(get_session)):
    user = None
    if access_token:
        username = auth.get_current_user(request)
        user = User(username=username)

    if user is None:
        return templates.TemplateResponse('auth/login_form.html',
                                          {'request': request,
                                           'user': user})
    peak_time = await db.execute(
        select(func.extract('hour', ParkingHistoryORM.start_time), func.count(ParkingHistoryORM.id))
        .group_by(func.extract('hour', ParkingHistoryORM.start_time))
        .order_by(func.count(ParkingHistoryORM.id).desc())
    )
    most_active_hour, count = peak_time.first()

    return {"most_active_hour": most_active_hour, "parking_count": count}


@router.get("/average_parking_duration_stats", response_class=HTMLResponse)
async def get_average_parking_duration_stats(request: Request, access_token: Annotated[Optional[str], Cookie()] = None,
                                             db: AsyncSession = Depends(get_session)):
    user = None
    if access_token:
        username = auth.get_current_user(request)
        user = User(username=username)

    if user is None:
        return templates.TemplateResponse('auth/login_form.html',
                                          {'request': request,
                                           'user': user})
    average_duration = await db.execute(
        select(func.avg(func.extract('epoch', ParkingHistoryORM.end_time - ParkingHistoryORM.start_time)))
        .where(ParkingHistoryORM.end_time.isnot(None))
    )
    average_duration_seconds = average_duration.scalar()

    average_duration_hours = average_duration_seconds / 3600 if average_duration_seconds else 0

    return {"average_parking_duration_hours": average_duration_hours}


@router.get("/parking_count_stats", response_class=HTMLResponse)
async def get_parking_count_stats(request: Request, access_token: Annotated[Optional[str], Cookie()] = None,
                                  db: AsyncSession = Depends(get_session), period: str = "day"):
    user = None
    if access_token:
        username = auth.get_current_user(request)
        user = User(username=username)

    if user is None:
        return templates.TemplateResponse('auth/login_form.html',
                                          {'request': request,
                                           'user': user})
    now = datetime.now()

    if period == "week":
        start_time = now - timedelta(weeks=1)
    elif period == "month":
        start_time = now - timedelta(days=30)
    else:
        start_time = now - timedelta(days=1)

    parking_count = await db.execute(
        select(func.count(ParkingHistoryORM.id)).where(ParkingHistoryORM.start_time >= start_time)
    )
    count = parking_count.scalar()

    return {"parking_count": count, "period": period}


@router.get("/available_spots_stats", response_class=HTMLResponse)
async def get_available_spots_stats(request: Request, access_token: Annotated[Optional[str], Cookie()] = None,
                                    db: AsyncSession = Depends(get_session)):
    user = None
    if access_token:
        username = auth.get_current_user(request)
        user = User(username=username)

    if user is None:
        return templates.TemplateResponse('auth/login_form.html',
                                          {'request': request,
                                           'user': user})
    occupied_spots = await db.execute(
        select(func.count(ParkingHistoryORM.id)).where(ParkingHistoryORM.end_time.is_(None))
    )
    occupied_spots_count = occupied_spots.scalar()

    available_spots = settings.TOTAL_SPOTS - occupied_spots_count

    return {"available_spots": available_spots}


@router.get("/average_car_parking_duration_stats", response_class=HTMLResponse)
async def get_average_car_parking_duration_stats(request: Request,
                                                 access_token: Annotated[Optional[str], Cookie()] = None,
                                                 db: AsyncSession = Depends(get_session)):
    user = None
    if access_token:
        username = auth.get_current_user(request)
        user = User(username=username)

    if user is None:
        return templates.TemplateResponse('auth/login_form.html',
                                          {'request': request,
                                           'user': user})
    average_duration = await db.execute(
        select(func.avg(func.extract('epoch', ParkingHistoryORM.end_time - ParkingHistoryORM.start_time)))
        .where(ParkingHistoryORM.end_time.isnot(None))
    )
    average_duration_seconds = average_duration.scalar()

    average_duration_hours = average_duration_seconds / 3600 if average_duration_seconds else 0

    return {"average_car_parking_duration_hours": average_duration_hours}
