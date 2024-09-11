from typing import Annotated, Any
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
# from db_models.models import User as UserModel
from db_models.orms import UserORM
from schemas.auth import UserLogin, UserCreate, User
from db_models.db import get_session

from frontend.routes import templates

auth = Authentication()
router = APIRouter(prefix="/auth",
                   tags=["Authentication"],
                   include_in_schema=False)


@router.get('/register')
async def get_register_form(response: Response,
                            request: Request):
    return templates.TemplateResponse('auth/register_form.html',
                                      context={'request': request})


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(request: Request,
                        username: Annotated[str, Form()],
                        email: Annotated[str, Form()],
                        password: Annotated[str, Form()],
                        db: AsyncSession = Depends(get_session)
                        ):
    user = UserCreate(username=username,
                      password=password,
                      email=email)
    stmnt = select(UserORM).where(UserORM.username == user.username)
    res = await db.execute(stmnt)
    existing_user = res.scalars().first()

    if existing_user:
        return templates.TemplateResponse(
            'auth/register_form.html',
            context={'request': request,
                     'error': 'Username already registered'})

    hashed_password = auth.get_password_hash(user.password)
    new_user = UserORM(username=user.username,
                       email=user.email,
                       password=hashed_password
                       )
    db.add(new_user)
    await db.commit()
    return templates.TemplateResponse('auth/registration_success.html',
                                      {'request': request,
                                       'username': new_user.username})


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
                                                   'error': 'User not found or invalid credentials'})
    user = User(username=username)
    ret = templates.TemplateResponse('user/user.html',
                                     {'request': request,
                                      'user': user})
    ret.set_cookie(key='access_token', value=result['access_token'])
    ret.set_cookie(key='refresh_token', value=result['refresh_token'])
    return ret


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


@router.get("/logout", response_model=dict)
async def logout_user(
        response: Response,
        request: Request
        ) -> Any:
    res = await auth.logout(response)
    user = None
    if res:
        ret = templates.TemplateResponse('index.html',
                                         {'request': request,
                                          'user': user})
        ret.delete_cookie('access_token')
        ret.delete_cookie('refresh_token')
        return ret
    
    return templates.TemplateResponse('index.html',
                                      {'request': request,
                                       'user': user})
