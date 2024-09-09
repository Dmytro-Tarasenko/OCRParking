# Routes for frontend endpoints

from pathlib import Path
from typing import Optional, Any, Annotated

from fastapi.routing import APIRouter
from fastapi import Request, Cookie, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter(include_in_schema=False)

templates_path = Path(__file__).parent / 'templates'

templates = Jinja2Templates(directory=str(templates_path))


@router.get('/')
async def index(
        request: Request
) -> Any:
    user = 'user'
    return templates.TemplateResponse('index.html', {'request': request,
                                                     'user': user})
