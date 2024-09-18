from typing import Annotated, Any, Optional
import re

from fastapi import Request, Response, Depends, Cookie, Form
from fastapi.routing import APIRouter
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from frontend.routes import templates
from auth.auth import Authentication
from schemas.auth import User
from schemas.cars import (
    CarInfo,
    BillingInfo,
    ParkingInfo,
    ParkingInfoExt,
    CarStatus,
    MessageInfo)
from db_models.orms import (
    UserORM,
    CarORM,
    ParkingHistoryORM,
    BillingORM,
    ServiceMessageORM
)
from db_models.db import get_session

NON_CHARS_REGEXP = r"[^a-zA-Z0-9]"

auth = Authentication()

router = APIRouter(prefix='/user',
                   default_response_class=HTMLResponse,
                   include_in_schema=False)


@router.get('/')
async def get_user_page(
        request: Request,
        db: Annotated[AsyncSession, Depends(get_session)],
        access_token: Annotated[str | None, Cookie()] = None
) -> Any:
    """
        Renders the user page if the user is authenticated, otherwise redirects to the login page.

        Args:
            request (Request): The current HTTP request object.
            db (AsyncSession): The asynchronous database session dependency.
            access_token (str | None, optional): The JWT access token stored in a cookie. Defaults to None.

        Returns:
            TemplateResponse: Renders the user page with user information if authenticated,
                              otherwise renders the login form.
        """
    user = None
    if access_token:
        username = auth.get_current_user(request)
        user = User(username=username)

    stmnt = select(UserORM).where(UserORM.username == user.username)
    res = await db.execute(stmnt)
    user_db = res.scalar_one_or_none()
    user.is_admin = user_db.is_admin

    return templates.TemplateResponse('user/user.html',
                                      {'request': request,
                                       'user': user})


async def get_car_status(
        db: AsyncSession,
        car_id: int
) -> CarStatus:
    """
        Retrieves the parking status of a car based on its car ID.

        Args:
            db (AsyncSession): The asynchronous database session dependency.
            car_id (int): The ID of the car to check its parking status.

        Returns:
            CarStatus: 'parked' if the car is currently parked, otherwise 'out'.
        """
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
    """
        Retrieves the list of cars owned by the authenticated user and displays their statuses.

        Args:
            request (Request): The current HTTP request object.
            db (AsyncSession): The asynchronous database session dependency.
            access_token (str | None, optional): The JWT access token stored in a cookie. Defaults to None.

        Returns:
            TemplateResponse: Renders the car list page if the user is authenticated, otherwise
                              renders the login form.
        """
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

    cars_info = zip(range(1, len(cars_info) + 1), cars_info)

    return templates.TemplateResponse('user/car_list.html',
                                      {'request': request,
                                       'cars': cars_info})


@router.get('/add_car')
async def get_add_car_form(
        request: Request,
        access_token: Annotated[str | None, Cookie()] = None
) -> Any:
    """Renders the 'Add Car' form if the user is authenticated.

        Args:
            request (Request): The HTTP request object.
            access_token (str, optional): The JWT access token stored in a cookie.
                Defaults to None.

        Returns:
            TemplateResponse: The 'login_form.html' if the user is not authenticated,
                otherwise the 'add_car_form.html' is rendered.
        """
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
    """Handles the submission of a new car registration by a user.

        Args:
            request (Request): The HTTP request object.
            db (AsyncSession): The database session for executing queries.
            car_plate (str): The car's license plate input from the form.
            access_token (Optional[str]): The JWT access token stored in a cookie.
                Defaults to None.

        Returns:
            TemplateResponse: Renders 'login_form.html' if the user is not authenticated,
                'add_car_form.html' with an error message if the car is already registered,
                or 'user.html' on successful car registration.
        """
    user = None
    car_plate = car_plate.upper()
    car_plate = re.sub(NON_CHARS_REGEXP, "", car_plate)
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
    """Displays the list of bills for the authenticated user.

        Args:
            request (Request): The HTTP request object.
            db (AsyncSession): The database session for executing queries.
            access_token (Optional[str]): The JWT access token stored in a cookie.
                Defaults to None.

        Returns:
            TemplateResponse: Renders 'login_form.html' if the user is not authenticated,
                otherwise renders 'bill_list.html' with the user's bills.
        """
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
        .where(BillingORM.user_id == user_db.id,
               BillingORM.is_sent.is_(True))
        .options(selectinload(BillingORM.user),
                 selectinload(BillingORM.history),
                 (selectinload(BillingORM.history)
                  .selectinload(ParkingHistoryORM.car))
                 )
    )
    res = await db.execute(stmnt)

    bills_db = res.scalars().all()
    bills_info = []
    for bill in bills_db:
        history = bill.history
        user = bill.user
        status = 'not issued'
        if bill.is_sent is True:
            status = 'sent'
        if bill.is_paid is True:
            status = 'paid'

        end_time = (history.end_time.strftime("%Y-%m-%d %H:%M:%S")
                    if history.end_time
                    else None)
        history_entry = ParkingInfo(
            car=history.car.car_plate,
            start_time=history.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            end_time=end_time
        )
        bill_entry = BillingInfo(id=bill.id,
                                 username=user.username,
                                 cost=round(bill.cost, 2),
                                 history=history_entry,
                                 status=status)
        bills_info.append(bill_entry)

    if len(bills_info) > 0:
        bills_info = zip(range(1, len(bills_info) + 1), bills_info)
    else:
        bills_info = None

    return templates.TemplateResponse('user/bill_list.html',
                                      {'request': request,
                                       'user': user,
                                       'bills': bills_info})


@router.get('/{car_plate:str}/bills')
async def get_car_bills(
        request: Request,
        db: Annotated[AsyncSession, Depends(get_session)],
        car_plate: str,
        access_token: Annotated[Optional[str], Cookie()] = None
) -> Any:
    """
        Retrieves and displays the billing information for a car associated with the
        currently authenticated user.

        Args:
            request (Request): The incoming request object.
            db (AsyncSession): The database session dependency.
            car_plate (str): The license plate of the car.
            access_token (Optional[str], optional): The JWT access token, retrieved from cookies. Defaults to None.

        Returns:
            Any: The response template rendering the car bills or an error message if the car is not registered
            under the user's account.

        Raises:
            HTTPException: If the car does not belong to the authenticated user.

        Notes:
            - If the user is not logged in, the login form will be displayed.
            - The user's bills are retrieved from the database and displayed along with relevant parking history.
        """
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

    stmnt = select(CarORM).where(
        CarORM.car_plate == car_plate,
        CarORM.user_id == user_db.id
    )
    res = await db.execute(stmnt)
    car_db = res.scalar_one_or_none()

    if car_db is None:
        return templates.TemplateResponse(
            'user/car_bills.html',
            {'request': request,
             'car': car_plate,
             'user': user,
             'error': f"Car {car_plate} is not registered for you."}
        )

    stmnt = (
        select(BillingORM)
        .join(ParkingHistoryORM)
        .where(ParkingHistoryORM.car_id == car_db.id,
               BillingORM.cost.is_not(None))
        .options(selectinload(BillingORM.history))
    )
    res = await db.execute(stmnt)
    bills_db = res.scalars().all()

    bills_info = []
    for bill in bills_db:
        history = bill.history
        user = bill.user

        status = 'not issued'
        if bill.is_sent is True:
            status = 'sent'
        if bill.is_paid is True:
            status = 'paid'

        end_time = (history.end_time.strftime("%Y-%m-%d %H:%M:%S")
                    if history.end_time
                    else None)
        history_entry = ParkingInfo(
            car=history.car.car_plate,
            start_time=history.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            end_time=end_time
        )
        bill_entry = BillingInfo(id=bill.id,
                                 username=user.username,
                                 cost=bill.cost,
                                 history=history_entry,
                                 status=status)
        bills_info.append(bill_entry)

    if len(bills_info) > 0:
        bills_info = zip(range(1, len(bills_info) + 1), bills_info)
    else:
        bills_info = None

    return templates.TemplateResponse('user/car_bills.html',
                                      {'request': request,
                                       'user': user,
                                       'car': car_plate,
                                       'bills': bills_info})


@router.get('/{car_plate:str}/parkings')
async def get_car_parkings(
        request: Request,
        db: Annotated[AsyncSession, Depends(get_session)],
        car_plate: str,
        access_token: Annotated[Optional[str], Cookie()] = None
) -> Any:
    """
        Retrieves and displays the parking history for a car associated with the
        currently authenticated user.

        Args:
            request (Request): The incoming request object.
            db (AsyncSession): The database session dependency.
            car_plate (str): The license plate of the car.
            access_token (Optional[str], optional): The JWT access token, retrieved from cookies. Defaults to None.

        Returns:
            Any: The response template rendering the car parkings or an error message if the car is not registered
            under the user's account.

        Raises:
            HTTPException: If the car does not belong to the authenticated user.

        Notes:
            - If the user is not logged in, the login form will be displayed.
            - The parking history is retrieved from the database and displayed with billing information.
        """
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

    stmnt = select(CarORM).where(
        CarORM.car_plate == car_plate,
        CarORM.user_id == user_db.id
    )
    res = await db.execute(stmnt)
    car_db = res.scalar_one_or_none()

    if car_db is None:
        return templates.TemplateResponse(
            'user/car_parkings.html',
            {'request': request,
             'car': car_plate,
             'user': user,
             'error': f"Car {car_plate} is not registered for you."}
        )

    stmnt = (
        select(ParkingHistoryORM)
        .where(ParkingHistoryORM.car_id == car_db.id)
        .options(
            selectinload(ParkingHistoryORM.bill),
            selectinload(ParkingHistoryORM.car)
        )
    )
    res = await db.execute(stmnt)
    parkings_db = res.scalars().all()

    parkings_info = []

    for parking in parkings_db:
        entry_bill = parking.bill
        entry_car = parking.car
        status = 'not issued'
        if entry_bill.is_sent is True:
            status = 'sent'
        if entry_bill.is_paid is True:
            status = 'paid'

        end_time = (parking.end_time.strftime("%Y-%m-%d %H:%M:%S")
                    if parking.end_time
                    else None)
        entry = ParkingInfoExt(
            car=entry_car.car_plate,
            start_time=parking.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            end_time=end_time,
            cost=entry_bill.cost,
            bill_id=entry_bill.id,
            status=status
        )
        parkings_info.append(entry)

    if len(parkings_info) > 0:
        parkings_info = zip(range(1, len(parkings_info) + 1), parkings_info)
    else:
        parkings_info = None

    return templates.TemplateResponse('user/car_parkings.html',
                                      {
                                          'request': request,
                                          'car': car_db.car_plate,
                                          'user': user,
                                          'parkings': parkings_info
                                      })


@router.get('/delete/{car_plate:str}')
async def get_car_delete_form(
        request: Request,
        car_plate: str,
        db: Annotated[AsyncSession, Depends(get_session)],
        access_token: Annotated[Optional[str], Cookie()] = None
) -> Any:
    """
        Renders a form to delete a user's car.

        Args:
            request (Request): The HTTP request object.
            car_plate (str): The license plate of the car to delete.
            db (AsyncSession): The database session for querying and interacting with the database.
            access_token (Optional[str], optional): JWT access token from a cookie, defaults to None.

        Returns:
            TemplateResponse: Renders a form to delete the car if the car exists and belongs to the user.
                              Otherwise, renders an error or login page.
        """
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

    stmnt = select(CarORM).where(
        CarORM.car_plate == car_plate,
        CarORM.user_id == user_db.id
    )
    res = await db.execute(stmnt)
    car_db = res.scalar_one_or_none()

    if car_db is None:
        return templates.TemplateResponse(
            'user/delete_car_form.html',
            {'request': request,
             'car': car_plate,
             'user': user,
             'error': f"Car {car_plate} is not registered for you."}
        )

    return templates.TemplateResponse(
        'user/delete_car_form.html',
        {
            'request': request,
            'user': user,
            'car': car_db.car_plate
        }
    )


@router.delete('/delete/{car_plate:str}')
async def delete_car(
        request: Request,
        car_plate: str,
        db: Annotated[AsyncSession, Depends(get_session)],
        access_token: Annotated[Optional[str], Cookie()] = None
) -> Any:
    """
        Deletes the user's car from the database if no unpaid bills exist.

        Args:
            request (Request): The HTTP request object.
            car_plate (str): The license plate of the car to delete.
            db (AsyncSession): The database session for querying and interacting with the database.
            access_token (Optional[str], optional): JWT access token from a cookie, defaults to None.

        Returns:
            TemplateResponse: Renders a confirmation page if the car is successfully deleted.
                              Otherwise, renders an error or login page.
        """
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

    stmnt = select(CarORM).where(
        CarORM.car_plate == car_plate,
        CarORM.user_id == user_db.id
    )
    res = await db.execute(stmnt)
    car_db = res.scalar_one_or_none()

    stmnt = (
        select(BillingORM)
        .join(ParkingHistoryORM)
        .where(
            BillingORM.is_paid.is_not(True),
            ParkingHistoryORM.car_id == car_db.id
        )
    )
    res = await db.execute(stmnt)
    bills_db = res.scalars().first()

    if bills_db:
        return templates.TemplateResponse(
            'user/car_deleted.html',
            {
                'request': request,
                'user': user,
                'error': f"Car {car_db.car_plate} could not be deleted due to unpaid bills."
            }
        )

    await db.delete(car_db)
    await db.commit()

    return templates.TemplateResponse(
        'user/car_deleted.html',
        {
            'request': request,
            'car': car_plate,
            'user': user
        }
    )


@router.get('/messages')
async def get_user_messages(
        request: Request,
        db: Annotated[AsyncSession, Depends(get_session)],
        access_token: Annotated[Optional[str], Cookie()] = None
) -> Any:
    """
        Retrieves and displays active messages for the current user.

        Args:
            request (Request): The HTTP request object.
            db (AsyncSession): The database session for querying and interacting with the database.
            access_token (Optional[str], optional): JWT access token from a cookie, defaults to None.

        Returns:
            TemplateResponse: Renders a list of active service messages for the user or prompts login if unauthorized.
        """
    user = None
    if access_token:
        username = auth.get_current_user(request)
        user = User(username=username)
    if user is None:
        return templates.TemplateResponse('auth/login_form.html',
                                          {'request': request,
                                           'user': user})

    stmnt = (
        select(ServiceMessageORM)
        .join(UserORM)
        .where(
            UserORM.username == user.username,
            ServiceMessageORM.is_active.is_(True)
        )
        .options(
            selectinload(ServiceMessageORM.bill)
        )
    )
    res = await db.execute(stmnt)

    messages_db = res.scalars().all()

    messages_info = [MessageInfo.model_validate(message)
                     for message in messages_db
                     if message.is_active is True]

    if len(messages_info) > 0:
        messages_info = zip(range(1, len(messages_info) + 1), messages_info)
    else:
        messages_info = None

    return templates.TemplateResponse(
        'user/message_list.html',
        {
            'user': user,
            'request': request,
            'messages': messages_info
        }
    )


@router.get('/paybill/{bill_id:int}')
async def get_paybill(
        request: Request,
        bill_id: int,
        db: Annotated[AsyncSession, Depends(get_session)],
        access_token: Annotated[Optional[str], Cookie()] = None
) -> Any:
    """
        Retrieve the billing details for a specific bill and render the payment page.

        Args:
            request (Request): The HTTP request object.
            bill_id (int): The ID of the bill to retrieve.
            db (AsyncSession): The asynchronous database session.
            access_token (Optional[str]): The access token stored in the user's cookies, used for authentication. Defaults to None.

        Returns:
            Any: A template response displaying the bill payment form if the user is authenticated, or the login form if not.

        Raises:
            None: This function does not raise any exceptions directly.

        Example:
            If the user is authenticated and the bill is found, a form with bill details is rendered for payment.
            If the user is not authenticated, a login form is presented.
        """
    user = None
    if access_token:
        username = auth.get_current_user(request)
        user = User(username=username)

    if user is None:
        return templates.TemplateResponse('auth/login_form.html',
                                          {'request': request,
                                           'user': user})

    stmnt = (
        select(BillingORM)
        .where(BillingORM.id == bill_id)
        .options(
            selectinload(BillingORM.history),
            selectinload(BillingORM.history).selectinload(ParkingHistoryORM.car)
        )
    )

    res = await db.execute(stmnt)
    bill_db = res.scalar_one_or_none()

    data = {
        'id': bill_db.id,
        'car_plate': bill_db.history.car.car_plate,
        'start': bill_db.history.start_time.strftime("%Y-%m-%d %H:%M:%S"),
        'end': bill_db.history.end_time.strftime("%Y-%m-%d %H:%M:%S"),
        'cost': bill_db.cost
    }

    return templates.TemplateResponse(
        'user/bill_payment.html',
        {
            'request': request,
            'user': user,
            'bill': data
        }
    )


@router.post('/paybill/{bill_id:int}')
async def post_paybill(
        request: Request,
        bill_id: int,
        db: Annotated[AsyncSession, Depends(get_session)],
        access_token: Annotated[Optional[str], Cookie()] = None
) -> Any:
    """
        Process the payment of a specific bill and update the bill status.

        Args:
            request (Request): The HTTP request object.
            bill_id (int): The ID of the bill to pay.
            db (AsyncSession): The asynchronous database session.
            access_token (Optional[str]): The access token stored in the user's cookies, used for authentication. Defaults to None.

        Returns:
            Any: A template response displaying the user dashboard after processing the payment, or the login form if the user is not authenticated.

        Raises:
            None: This function does not raise any exceptions directly.

        Example:
            If the payment is successful, the bill is marked as paid, and any bans related to unpaid bills are removed.
            If the user is not authenticated, a login form is presented.
        """
    user = None
    if access_token:
        username = auth.get_current_user(request)
        user = User(username=username)

    if user is None:
        return templates.TemplateResponse('auth/login_form.html',
                                          {'request': request,
                                           'user': user})

    stmnt = (
        select(BillingORM)
        .where(BillingORM.id == bill_id)
        .options(
            selectinload(BillingORM.message),
            selectinload(BillingORM.user)
        )
    )

    res = await db.execute(stmnt)
    bill_db = res.scalars().first()

    bill_db.is_paid = True
    bill_db.message.is_active = False
    bill_is_ban = bill_db.is_ban

    await db.commit()

    if bill_is_ban:
        stmnt = (
            select(UserORM)
            .join(BillingORM)
            .where(
                UserORM.username == user.username,
                BillingORM.is_ban.is_(True),
                BillingORM.is_paid.is_not(True)
            )
        )

        res = await db.execute(stmnt)
        user_db = res.scalars().first()

        if user_db is None:
            stmnt = select(UserORM).where(UserORM.username == user.username)
            res = await db.execute(stmnt)
            user_db = res.scalar_one()
            user_db.is_banned = False

    await db.commit()

    return templates.TemplateResponse(
        'user/user.html',
        {
            'request': request,
            'user': user
        }
    )
