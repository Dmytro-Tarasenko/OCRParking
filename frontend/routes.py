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
        user = 'user'
    return templates.TemplateResponse('index.html', {'request': request,
                                                     'user': user})
