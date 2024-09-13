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

router = APIRouter(prefix='/cameras',
                   default_response_class=HTMLResponse,
                   include_in_schema=False)


@router.get('/')
async def cameras_index(
    request: Request
) -> Any:
    return templates.TemplateResponse('cameras/cameras.html',
                                      {'request': request})