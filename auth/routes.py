from typing import Annotated
from fastapi import (APIRouter,
                     Depends,
                     HTTPException,
                     Response,
                     status,
                     Request,
                     Form)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from auth.auth import Authentication
from db_models.models import User as UserModel
from schemas.auth import UserLogin, UserCreate
from db_models.db import get_session

from frontend.routes import templates

auth = Authentication()
router = APIRouter(prefix="/auth",
                   tags=["Authentication"],
                   include_in_schema=False)



@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate,
                        db: AsyncSession = Depends(get_session)
                        ):
    existing_user = await db.execute(select(UserModel).where(UserModel.username == user.username))
    if existing_user.scalar():
        raise HTTPException(status_code=400,
                            detail="Username already registered")

    hashed_password = auth.get_password_hash(user.password)
    new_user = UserModel(username=user.username,
                         email=user.email,
                         password=hashed_password
                         )
    db.add(new_user)
    await db.commit()
    return {"msg": "User registered successfully"}

@router.get("/login")
async def get_login_form(response: Response,
                         request: Request):

    return templates.TemplateResponse('auth/login_form.html',
                                      context={'request': request})


@router.post("/login")
async def login(response: Response,
                request: Request,
                username: Annotated[str, Form()],
                password: Annotated[str, Form()],
                db: AsyncSession = Depends(get_session)):
    user_login = UserLogin(username=username,
                           password=password)
    result = await auth.login(response, user_login, db)
    if not result:
        return templates.TemplateResponse('auth/login_form.html',
                                          context={'request': request,
                                                   'error': 'User not found.'})
    return result


@router.post("/refresh")
async def refresh_token(response: Response, request: Request):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token found")
    result = await auth.refresh_token(response, refresh_token)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    return result


@router.get("/admin")
async def admin_route(request: Request, db: AsyncSession = Depends(get_session)):
    user = await auth.is_admin(request, db)
    return {"msg": f"Hello, {user.username}. You are an admin!"}


@router.post("/logout", response_model=dict)
async def logout_user(
        response: Response):

    return await auth.logout(response)
