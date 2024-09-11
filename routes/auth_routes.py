from fastapi import (APIRouter,
                     Depends,
                     Response,
                     status,
                     Request)
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from routes.auth import Authentication
from db_models.models import User as UserModel
from schemas.auth import UserCreate
from db_models.db import get_session

auth = Authentication()
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_session)):
    existing_user = await db.execute(select(UserModel).where(UserModel.username == user.username))
    if existing_user.scalar():
        return {"error": "Username already registered"}

    hashed_password = auth.get_password_hash(user.password)
    new_user = UserModel(username=user.username, email=user.email, password=hashed_password)
    db.add(new_user)
    await db.commit()
    return {"msg": "User registered successfully"}


@router.post("/login")
async def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends(),
                db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(UserModel).where(UserModel.username == form_data.username))
    user = result.scalar()

    if not user:
        return JSONResponse(status_code=400, content={"detail": "Incorrect username or password"})

    if not auth.verify_password(form_data.password, user.password):
        return JSONResponse(status_code=400, content={"detail": "Incorrect username or password"})

    access_token = auth.create_access_token(data={"sub": user.username})
    refresh_token = auth.create_refresh_token(data={"sub": user.username})
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    response.set_cookie(key="refresh_token", value=f"Bearer {refresh_token}", httponly=True)

    return {"access_token": access_token, "refresh_token": refresh_token}


@router.post("/refresh")
async def refresh_token_route(response: Response, request: Request):
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        return {"error": "No refresh token found"}
    result = await auth.refresh_token(response, refresh_token)

    if "error" in result:
        return result

    return result


@router.get("/is_admin")
async def admin_route(request: Request, db: AsyncSession = Depends(get_session)):
    user = await auth.is_admin(request, db)

    if isinstance(user, dict) and "error" in user:
        return user

    return {"msg": f"Hello, {user.username}. You are an admin!"}


@router.post("/logout", response_model=dict)
async def logout_user(request: Request, response: Response):
    return await auth.logout(request, response)
