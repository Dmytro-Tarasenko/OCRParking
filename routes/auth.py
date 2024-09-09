from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, Response, Request, security
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from schemas.auth import UserLogin
from db_models.models import User as UserModel
from settings import settings


class Authentication:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    oauth2_schema = security.OAuth2PasswordBearer(tokenUrl="token")
    # oauth2_schema = security.OAuth2PasswordBearer(tokenUrl="/auth/login")

    def get_password_hash(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    def create_access_token(self, data: dict, expires_delta: timedelta | None = None) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.SECRET, algorithm=settings.ALGORITHM)

    def create_refresh_token(self, data: dict, expires_delta: timedelta | None = None) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, settings.REFRESH_SECRET, algorithm=settings.ALGORITHM)

    def decode_token(self, token: str, secret_key: str) -> str:
        try:
            payload = jwt.decode(token, secret_key, algorithms=[settings.ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise HTTPException(status_code=401, detail="Could not validate credentials")
            return username
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

    async def authenticate_user(self, username: str, password: str, db: AsyncSession) -> UserModel | None:
        result = await db.execute(select(UserModel).where(UserModel.username == username))
        user = result.scalar()
        if user and self.verify_password(password, user.password):
            return user
        return None

    async def login(self, response: Response, user_login: UserLogin, db: AsyncSession) -> dict:
        user = await self.authenticate_user(user_login.username, user_login.password, db)
        if not user:
            raise HTTPException(status_code=400, detail="Invalid username or password")

        access_token = self.create_access_token(data={"sub": user.username})
        refresh_token = self.create_refresh_token(data={"sub": user.username})

        response.set_cookie(key="access_token", value=access_token, httponly=True)
        response.set_cookie(key="refresh_token", value=refresh_token, httponly=True)

        return {"access_token": access_token, "refresh_token": refresh_token}

    async def refresh_token(self, response: Response, refresh_token: str) -> dict:

        username = self.decode_token(refresh_token, settings.REFRESH_SECRET)
        new_access_token = self.create_access_token(data={"sub": username})
        new_refresh_token = self.create_refresh_token(data={"sub": username})

        response.set_cookie(key="access_token", value=new_access_token, httponly=True)
        response.set_cookie(key="refresh_token", value=new_refresh_token, httponly=True)

        return {"access_token": new_access_token, "refresh_token": new_refresh_token}

    def get_current_user(self, request: Request) -> str:
        token = request.cookies.get("access_token")
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        return self.decode_token(token, settings.SECRET)

    async def is_admin(self, request: Request, db: AsyncSession) -> UserModel:
        token = request.cookies.get("access_token")
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")

        username = self.decode_token(token, settings.SECRET)
        result = await db.execute(select(UserModel).where(UserModel.username == username))
        user = result.scalar()
        if not user or not user.is_admin:
            raise HTTPException(status_code=403, detail="Not enough privileges")
        return user

    async def logout(self, response: Response):

        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")

        return {"detail": "Logged out successfully"}
