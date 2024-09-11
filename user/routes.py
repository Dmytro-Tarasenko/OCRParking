from typing import Annotated, Any, Optional

from fastapi import Request, Response, Depends, Cookie, Form
from fastapi.routing import APIRouter
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from frontend.routes import templates
from auth.auth import Authentication
from schemas.auth import User
from schemas.cars import CarInfo, CarStatus, BillingInfo, ParkingInfo
from db_models.orms import UserORM, CarORM, ParkingHistoryORM, BillingORM
from db_models.db import get_session

auth = Authentication()

router = APIRouter(prefix='/user',
                   default_response_class=HTMLResponse,
                   include_in_schema=False)


@router.get('/')
def get_user_page(
    request: Request,
    access_token: Annotated[str | None, Cookie()] = None
) -> Any:
    user = None
    if access_token:
        username = auth.get_current_user(request)
        user = User(username=username)
    return templates.TemplateResponse('user/user.html',
                                      {'request': request,
                                       'user': user})


async def get_car_status(
        db: AsyncSession,
        car_id: int
        ) -> CarStatus:
    stmnt = (
        select(ParkingHistoryORM)
        .where(ParkingHistoryORM.car_id == car_id,
               ParkingHistoryORM.start_time.is_not(None),
               ParkingHistoryORM.end_time.is_(None)
               )
    )
    res = await db.execute(stmnt)
    parked_car = res.scalar_one_or_none()

    if parked_car:
        return 'parked'
    return 'out'


@router.get('/my_cars')
async def get_user_cars(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_session)],
    access_token: Annotated[str | None, Cookie()] = None
) -> Any:
    user = None
    if access_token:
        username = auth.get_current_user(request)
        user = User(username=username)

    if user is None:
        return templates.TemplateResponse('auth/login_form.html',
                                          {'request': request,
                                           'user': user})
    stmnt = (
        select(UserORM).where(UserORM.username == user.username)
        .options(selectinload(UserORM.cars))
        )
    res = await db.execute(stmnt)
    cars_db = res.scalar().cars
    cars_info = []
    for car in cars_db:
        status = await get_car_status(db, car.id)
        cars_info.append(CarInfo(car_plate=car.car_plate,
                                 status=status))

    cars_info = zip(range(1, len(cars_info)+1), cars_info)

    return templates.TemplateResponse('user/car_list.html',
                                      {'request': request,
                                       'cars': cars_info})


@router.get('/add_car')
async def get_add_car_form(
    request: Request,
    access_token: Annotated[str | None, Cookie()] = None
) -> Any:
    user = None
    if access_token:
        username = auth.get_current_user(request)
        user = User(username=username)

    if user is None:
        return templates.TemplateResponse('auth/login_form.html',
                                          {'request': request,
                                           'user': user})

    return templates.TemplateResponse('user/add_car_form.html',
                                      {'request': request,
                                       'user': user})


@router.post('/add_car')
async def post_add_car(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_session)],
    car_plate: Annotated[str, Form()],
    access_token: Annotated[Optional[str], Cookie()] = None
) -> Any:
    user = None
    if access_token:
        username = auth.get_current_user(request)
        user = User(username=username)

    if user is None:
        return templates.TemplateResponse('auth/login_form.html',
                                          {'request': request,
                                           'user': user})
    stmnt = select(CarORM).where(CarORM.car_plate == car_plate)
    res = await db.execute(stmnt)
    car = res.scalar_one_or_none()
    if car:
        return templates.TemplateResponse(
            'user/add_car_form.html',
            {'request': request,
             'user': user,
             'error': f"Car with {car.car_plate} already registered."})

    stmnt = select(UserORM).where(UserORM.username == user.username)
    res = await db.execute(stmnt)
    user_db = res.scalar_one()
    new_car = CarORM(car_plate=car_plate)
    new_car.owner = user_db
    db.add(new_car)
    await db.commit()
    return templates.TemplateResponse('user/user.html',
                                      {'request': request,
                                       'user': user})


@router.get('/my_bills')
async def get_user_bills(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_session)],
    access_token: Annotated[Optional[str], Cookie()] = None
) -> Any:
    user = None
    if access_token:
        username = auth.get_current_user(request)
        user = User(username=username)
    if user is None:
        return templates.TemplateResponse('auth/login_form.html',
                                          {'request': request,
                                           'user': user})

    stmnt = select(UserORM).where(UserORM.username == user.username)
    res = await db.execute(stmnt)
    user_db = res.scalar_one_or_none()

    stmnt = (
        select(BillingORM)
        .where(BillingORM.user_id == user_db.id)
        .options(selectinload(BillingORM.user),
                 selectinload(BillingORM.history)
                 )
        )
    res = await db.execute(stmnt)

    bills_db = res.scalars().all()
    bills_info = []
    for bill in bills_db:
        history = bill.history
        user = bill.user
        history_entry = ParkingInfo(car=history.car,
                                    start_time=history.start_time,
                                    end_time=history.end_time)
        bill_entry = BillingInfo(username=user.username,
                                 cost=bill.cost,
                                 history=history_entry,
                                 is_paid=bill.is_paid)
        bills_info.append(bill_entry)

    if len(bills_info) > 0:
        bills_info = zip(range(1, len(bills_info)+1), bills_info)
    else:
        bills_info = None

    return templates.TemplateResponse('user/bill_list.html',
                                      {'request': request,
                                       'user': user,
                                       'bills': bills_info})
