import re
from typing import Annotated, Any
from datetime import datetime

from fastapi import Request, Depends, Form, UploadFile, File
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
from ocr_ml.plate_recognition import get_plate_number


CAR_PLATE_REGEX = r"[^0-9A-Z]"

router = APIRouter(prefix='/cameras',
                   default_response_class=HTMLResponse,
                   include_in_schema=False)


@router.get('/')
async def cameras_index(
    request: Request
) -> Any:
    """Renders the cameras index page.

        This asynchronous function handles GET requests to the root path of the cameras route.
        It returns an HTML response rendering the 'cameras/cameras.html' template.

        Args:
            request (Request): The request object representing the current HTTP request.

        Returns:
            Any: A response object containing the rendered template and the request context.
        """
    return templates.TemplateResponse('cameras/cameras.html',
                                      {'request': request})


@router.post('/enter')
async def post_enter_camera(
    request: Request,
    car_plate: Annotated[UploadFile, File()],
    db: Annotated[AsyncSession, Depends(get_session)]
) -> Any:
    """
        Handle car entry through the camera system.

        This endpoint processes the image of the car's license plate, checks the user's
        registration and status, and determines whether the car should be allowed entry.
        Depending on the result of the checks, the system raises the barrier or keeps it down.

        Args:
            request (Request): The incoming HTTP request object.
            car_plate (UploadFile): The uploaded image file containing the car's license plate.
            db (AsyncSession): Database session for querying the relevant data.

        Returns:
            Any: The HTML response template indicating if the barrier is raised or not.

        Raises:
            HTTPException: If there are issues with accessing or querying the database.

        Process:
            1. Reads the car plate image and extracts the plate number.
            2. Verifies if the car is registered in the system.
            3. Checks if the user is banned.
            4. If the car is already parked, generates a bill and bans the user for attempting
               to re-enter without leaving.
            5. Logs the parking entry, generates a bill for the session, and raises the barrier.

        Templates:
            - 'cameras/turnpike_down.html': Displayed if the car is unregistered, banned,
              or attempting unauthorized re-entry.
            - 'cameras/turnpike_up.html': Displayed when the car passes all checks, and the
              barrier is raised for entry.

        Examples:
            Post a request with an uploaded car plate image:

            ```python
            async def enter_camera_route():
                form_data = {'car_plate': open('car_image.jpg', 'rb')}
                response = await client.post('/enter', files=form_data)
                assert response.status_code == 200
            ```
        """
    image = await car_plate.read()
    car_plates = get_plate_number(image)

    car_plate = ""
    is_user = False
    for plate in car_plates:
        car_plate = re.sub(CAR_PLATE_REGEX, "", plate.text)
        is_user = await utils.is_user(car_plate.upper(), db)
        if is_user:
            break

    if not is_user:
        return templates.TemplateResponse(
           'cameras/turnpike_down.html',
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
            'cameras/turnpike_down.html',
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
           'cameras/turnpike_down.html',
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

    await utils.occupy_lot(car_db.id, db)

    return templates.TemplateResponse(
        'cameras/turnpike_up.html',
        {
            'request': request
            }
        )


@router.post('/leave')
async def post_leave_camera(
    request: Request,
    car_plate: Annotated[UploadFile, File()],
    db: Annotated[AsyncSession, Depends(get_session)]
) -> Any:
    """
        Processes a car leaving the parking area.

        This function receives an uploaded image from the exit camera, detects the car's
        license plate, and performs several checks:
        - If the car is registered in the system.
        - If the car owner is banned.
        - If the car's entry into the parking area was registered.

        Depending on the results, it will either raise the barrier for the car to leave,
        or deny exit with a message.

        Args:
            request (Request): The HTTP request object.
            car_plate (UploadFile): The uploaded image file containing the car's plate.
            db (AsyncSession): The database session for performing queries.

        Returns:
            Any: Renders an HTML template response, either allowing the car to leave or
            returning an error message.

        Raises:
            HTTPException: If there is an issue with the database or car registration.
        """
    image = await car_plate.read()
    car_plates = get_plate_number(image)

    car_plate = ""
    is_user = False
    for plate in car_plates:
        car_plate = re.sub(CAR_PLATE_REGEX, "", plate.text)
        is_user = await utils.is_user(car_plate.upper(), db)
        if is_user:
            break

    if not is_user:
        return templates.TemplateResponse(
           'cameras/turnpike_down.html',
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
            'cameras/turnpike_down.html',
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
           'cameras/turnpike_down.html',
           {
               'request': request,
               'error': (f"Car {car_plate} registered as out from parking."
                         + f" Bill #{bill_id} is sent."
                         + f" User banned (message # {message_id}).")
           }
        )

    stmnt = (
        select(ParkingHistoryORM)
        .where(ParkingHistoryORM.car_id == car_db.id,
               ParkingHistoryORM.end_time.is_(None))
               .options(
                   selectinload(ParkingHistoryORM.bill)
               )
        )
    res = await db.execute(stmnt)
    parking_db = res.scalar_one_or_none()
    end_time = datetime.now()
    parking_db.end_time=end_time

    tariff = await utils.get_tariff_for_date(
        parking_db.start_time,
        db)

    time_diff_minutes = (
        (parking_db.end_time - parking_db.start_time).seconds // 60
    )

    cost = round(time_diff_minutes * tariff, 2)
    parking_db.bill.cost = cost
    parking_db.bill.is_sent = True

    await utils.send_message(car_db.owner.id,
                             parking_db.bill.id,
                             db)
    
    await utils.free_lot(car_db.id, db)
    
    await db.commit()

    return templates.TemplateResponse(
        'cameras/turnpike_up.html',
        {
            'request': request
            }
        )


@router.get('/turnpike_down')
async def get_turnpike_down(
    request: Request
) -> Any:
    """Renders the 'turnpike_down' HTML page.

        This endpoint returns an HTML page that displays the state when the
        turnpike is down. It uses FastAPI's template rendering system.

        Args:
            request (Request): The HTTP request object.

        Returns:
            Any: A TemplateResponse object that renders the 'turnpike_down.html'
            template with the given request.
        """
    return templates.TemplateResponse(
        'cameras/turnpike_down.html',
        {'request': request}
    )