# Routes for frontend endpoints

from pathlib import Path
from typing import Any, Annotated

from fastapi.routing import APIRouter
from fastapi import Request, Cookie, Depends
# from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
# from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db_models.db import get_session
from auth.auth import Authentication
from schemas.auth import User

auth = Authentication()

router = APIRouter(include_in_schema=False)

templates_path = Path(__file__).parent / 'templates'

templates = Jinja2Templates(directory=str(templates_path))


@router.get('/')
async def index(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_session)],
    access_token: Annotated[str | None, Cookie()] = None,
) -> Any:
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
    user = None
    if access_token:
        username = auth.get_current_user(request)
        user = User(username=username)
    return templates.TemplateResponse('about.html', {'request': request,
                                                     'user': user})
