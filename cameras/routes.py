from typing import Annotated, Any, Optional

from fastapi import Request, Response, Depends, Form
from fastapi.routing import APIRouter
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from frontend.routes import templates
from user.routes import get_car_status
from schemas.cars import CarInfo, CarStatus, BillingInfo, ParkingInfo
from db_models.orms import UserORM, CarORM, ParkingHistoryORM, BillingORM
from db_models.db import get_session

import cameras.utils as utils


router = APIRouter(prefix='/cameras',
                   default_response_class=HTMLResponse,
                   include_in_schema=False)


@router.get('/')
async def cameras_index(
    request: Request
) -> Any:
    return templates.TemplateResponse('cameras/cameras.html',
                                      {'request': request})


@router.post('/enter')
async def post_enter_camera(
    request: Request,
    car_plate: Annotated[str, Form()],
    db: Annotated[AsyncSession, Depends(get_session)]
) -> Any:
    car_plate = car_plate.upper()
    is_user = await utils.is_user(car_plate, db)

    if not is_user:
        return templates.TemplateResponse(
           'cameras/cameras.html',
           {
               'request': request,
               'error': f"Car {car_plate} does not registered."
           }
        )
    is_banned = await utils.is_banned(car_plate, db)

    if is_banned:
        stmnt = (
            select(CarORM)
            .where(CarORM.car_plate == car_plate)
            .options(
                selectinload(CarORM.owner)
            )
        )
        res = await db.execute(stmnt)
        car_db = res.scalar_one()

        return templates.TemplateResponse(
            'cameras/cameras.html',
            {
                'request': request,
                'error': f"User {car_db.owner.username} is banned!"
            }
        )

    stmnt = (
        select(CarORM)
        .where(CarORM.car_plate == car_plate)
        .options(
            selectinload(CarORM.owner)
            )
        )
    res = await db.execute(stmnt)
    car_db = res.scalar_one()

    car_status = await get_car_status(db, car_db.id)

    if car_status == 'parked':
        bill_id = await utils.set_unleaved_ban(car_db, db)
        ban_message = "Заїзд автомобіля без зареєстрованого виїзду."
        message_id = await utils.send_ban_message(car_db.owner.id,
                                                  bill_id,
                                                  ban_message,
                                                  db)
        return templates.TemplateResponse(
           'cameras/cameras.html',
           {
               'request': request,
               'error': (f"Car {car_plate} registered as parked."
                         + f" Bill #{bill_id} is sent."
                         + f" User banned (message # {message_id}).")
           }
        )

    parking = ParkingHistoryORM(
        car_id=car_db.id
    )
    db.add(parking)
    await db.commit()

    new_bill = BillingORM(
        user_id=car_db.owner.id
    )

    parking.bill = new_bill
    db.refresh(parking)
    await db.commit()

    # TODO: Turnpike action
    return templates.TemplateResponse(
        'cameras/cameras.html',
        {
            'request': request
            }
        )


@router.post('/leave')
async def post_leave_camera(
    request: Request,
    car_plate: Annotated[str, Form()],
    db: Annotated[AsyncSession, Depends(get_session)]
) -> Any:
    car_plate = car_plate.upper()
    is_user = await utils.is_user(car_plate, db)

    if not is_user:
        return templates.TemplateResponse(
           'cameras/cameras.html',
           {
               'request': request,
               'error': f"Car {car_plate} does not registered."
           }
        )
    is_banned = await utils.is_banned(car_plate, db)

    if is_banned:
        stmnt = (
            select(CarORM)
            .where(CarORM.car_plate == car_plate)
            .options(
                selectinload(CarORM.owner)
            )
        )
        res = await db.execute(stmnt)
        car_db = res.scalar_one()

        return templates.TemplateResponse(
            'cameras/cameras.html',
            {
                'request': request,
                'error': f"User {car_db.owner.username} is banned!"
            }
        )

    stmnt = (
        select(CarORM)
        .where(CarORM.car_plate == car_plate)
        .options(
            selectinload(CarORM.owner)
            )
        )
    res = await db.execute(stmnt)
    car_db = res.scalar_one()

    car_status = await get_car_status(db, car_db.id)

    if car_status == 'out':
        bill_id = await utils.set_unparked_ban(car_db, db)
        ban_message = "Виїзд автомобіля без зареєстрованого в'їзду."
        message_id = await utils.send_ban_message(car_db.owner.id,
                                                  bill_id,
                                                  ban_message,
                                                  db)
        return templates.TemplateResponse(
           'cameras/cameras.html',
           {
               'request': request,
               'error': (f"Car {car_plate} registered as out from parking."
                         + f" Bill #{bill_id} is sent."
                         + f" User banned (message # {message_id}).")
           }
        )

    # TODO: Set end_time and billing info
    parking = ParkingHistoryORM(
        car_id=car_db.id
    )
    db.add(parking)
    await db.commit()

    new_bill = BillingORM(
        user_id=car_db.owner.id
    )

    parking.bill = new_bill
    db.refresh(parking)
    await db.commit()

    # TODO: Turnpike action
    return templates.TemplateResponse(
        'cameras/cameras.html',
        {
            'request': request
            }
        )
