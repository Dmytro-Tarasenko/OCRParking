from pathlib import Path
from typing import Any, Annotated

from fastapi.routing import APIRouter
from fastapi import Request, Cookie, Depends
from fastapi.templating import Jinja2Templates

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db_models.db import get_session
from db_models.orms import ParkingLotORM
from auth.auth import Authentication
from schemas.auth import User
from schemas.cars import ParkingLot

auth = Authentication()

router = APIRouter(include_in_schema=True)

templates_path = Path(__file__).parent / 'templates'

templates = Jinja2Templates(directory=str(templates_path))


@router.get('/')
async def index(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_session)],
    access_token: Annotated[str | None, Cookie()] = None,
) -> Any:
    """
        Render the index page.

        This route handles rendering the index page. If an access token is present
        in the cookies, it extracts the current user and passes the user information
        to the template. Otherwise, the user will be `None`.

        Args:
            request (Request): The HTTP request object.
            db (AsyncSession): The database session for handling database operations.
            access_token (str | None, optional): The access token stored in cookies.
                Defaults to None.

        Returns:
            TemplateResponse: The rendered 'index.html' template with the request and user data.
        """
    user = None
    if access_token:
        username = auth.get_current_user(request)
        user = User(username=username)
    return templates.TemplateResponse('index.html', {'request': request,
                                                     'user': user})


@router.get('/about')
async def about(
    request: Request,
    access_token: Annotated[str | None, Cookie()] = None,
):
    """
        Render the about page.

        This route handles rendering the about page. If an access token is present
        in the cookies, it extracts the current user and passes the user information
        to the template. Otherwise, the user will be `None`.

        Args:
            request (Request): The HTTP request object.
            access_token (str | None, optional): The access token stored in cookies.
                Defaults to None.

        Returns:
            TemplateResponse: The rendered 'about.html' template with the request and user data.
        """
    user = None
    if access_token:
        username = auth.get_current_user(request)
        user = User(username=username)
    return templates.TemplateResponse('about.html', {'request': request,
                                                     'user': user})


@router.get('/parking_lots')
async def get_parking_lots(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_session)]
) -> Any:
    """
        Fetches and returns parking lot information, including occupied, free, and total spaces.

        The function retrieves all parking lots from the database, processes the data,
        and calculates the number of free and occupied parking spaces. It returns
        an HTML response with the template 'lots.html' and the parking information.

        Args:
            request (Request): The HTTP request object.
            db (Annotated[AsyncSession, Depends]): The database session to execute the queries.

        Returns:
            TemplateResponse: An HTML response with the parking lot information
            (total spaces, free spaces, occupied spaces) and a list of parking lots.
        """
    stmnt = select(ParkingLotORM).order_by(ParkingLotORM.id)
    res = await db.execute(stmnt)
    lots_db = res.scalars().all()

    lots_info = []
    for lot in lots_db:
        entry = ParkingLot.model_validate(lot)
        lots_info.append(entry)
    
    stmnt = select(ParkingLotORM).where(ParkingLotORM.car_id.is_not(None))
    res = await db.execute(stmnt)
    occupied = len(res.scalars().all())
    free = 30 - occupied
    total = 30

    return templates.TemplateResponse(
        'lots.html',
        {
            'request': request,
            'lots': lots_info,
            'occupied': occupied,
            'free': free,
            'total': total
        }
    )