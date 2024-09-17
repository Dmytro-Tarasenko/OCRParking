from datetime import datetime, timedelta
from jose import jwt, JWTError
import bcrypt
from fastapi import HTTPException, Response, Request, security
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from schemas.auth import UserLogin
from db_models.models import User as UserModel
from settings import settings


class Authentication:
    """
        Authentication class responsible for user authentication, token generation,
        and authorization for the OCRParking system.

        Attributes:
            hash_service (bcrypt): Service for password hashing and verification.
            oauth2_schema (OAuth2PasswordBearer): Security schema for handling OAuth2 password tokens.
        """
    # pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hash_service = bcrypt
    oauth2_schema = security.OAuth2PasswordBearer(tokenUrl="token")

    # oauth2_schema = security.OAuth2PasswordBearer(tokenUrl="/auth/login")

    def get_password_hash(self, password: str) -> str:
        """
                Hashes the given password using bcrypt.

                Args:
                    password (str): The plaintext password to be hashed.

                Returns:
                    str: The hashed password.
                """
        return self.hash_service.hashpw(
            password=password.encode(),
            salt=self.hash_service.gensalt()
        ).decode()

    def verify_password(
            self,
            plain_password: str,
            hashed_password: str
    ) -> bool:
        """
                Verifies a password against its hashed version.

                Args:
                    plain_password (str): The plaintext password.
                    hashed_password (str): The hashed password for comparison.

                Returns:
                    bool: True if the password matches, False otherwise.
                """

        return self.hash_service.checkpw(
            password=plain_password.encode(),
            hashed_password=hashed_password.encode()
        )

    def create_access_token(self,
                            data: dict,
                            expires_delta: timedelta | None = None
                            ) -> str:
        """
                Creates a JWT access token.

                Args:
                    data (dict): The data to encode in the token, typically user identification.
                    expires_delta (timedelta, optional): The token expiration time. Defaults to settings.

                Returns:
                    str: The encoded JWT token.
                """
        to_encode = data.copy()
        expire = (
                datetime.now()
                + (expires_delta
                   or timedelta(minutes=settings.access_token_expire_minutes))
        )
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode,
                          settings.secret,
                          algorithm=settings.algorithm)

    def create_refresh_token(self,
                             data: dict,
                             expires_delta: timedelta | None = None
                             ) -> str:
        """
                Creates a JWT refresh token.

                Args:
                    data (dict): The data to encode in the token, typically user identification.
                    expires_delta (timedelta, optional): The token expiration time. Defaults to settings.

                Returns:
                    str: The encoded JWT refresh token.
                """
        to_encode = data.copy()
        expire = (
                datetime.now()
                + (expires_delta
                   or timedelta(minutes=settings.refresh_token_expire_days))
        )
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode,
                          settings.refresh_secret,
                          algorithm=settings.algorithm)

    def decode_token(self, token: str, secret_key: str) -> str:
        """
                Decodes a JWT token and retrieves the username from the payload.

                Args:
                    token (str): The JWT token to decode.
                    secret_key (str): The key used to decode the token.

                Returns:
                    str: The username (subject) encoded in the token.

                Raises:
                    HTTPException: If the token is invalid or missing the 'sub' field.
                """
        try:
            payload = jwt.decode(token,
                                 secret_key,
                                 algorithms=[settings.algorithm])
            username: str = payload.get("sub")
            if username is None:
                raise HTTPException(status_code=401,
                                    detail="Could not validate credentials")
            return username
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

    async def authenticate_user(self,
                                username: str,
                                password: str,
                                db: AsyncSession
                                ) -> UserModel | None:
        """
                Authenticates a user by verifying the username and password.

                Args:
                    username (str): The username of the user.
                    password (str): The plaintext password of the user.
                    db (AsyncSession): The database session.

                Returns:
                    UserModel | None: The authenticated user or None if authentication fails.
                """
        result = await db.execute(select(UserModel).where(UserModel.username == username))
        user = result.scalar()
        if user and self.verify_password(password, user.password):
            return user
        return None

    async def login(self,
                    response: Response,
                    user_login: UserLogin,
                    db: AsyncSession) -> dict:
        """
                Handles user login by generating access and refresh tokens and setting cookies.

                Args:
                    response (Response): The response object to set cookies.
                    user_login (UserLogin): The login data (username and password).
                    db (AsyncSession): The database session.

                Returns:
                    dict: A dictionary containing the access and refresh tokens.
                """
        user = await self.authenticate_user(user_login.username,
                                            user_login.password,
                                            db)
        if not user:
            return {"msg": "Incorrect username or password"}

        access_token = self.create_access_token(data={"sub": user.username})
        refresh_token = self.create_refresh_token(data={"sub": user.username})

        response.set_cookie(key="access_token",
                            value=access_token,
                            httponly=True)
        response.set_cookie(key="refresh_token",
                            value=refresh_token,
                            httponly=True)

        return {"access_token": access_token,
                "refresh_token": refresh_token}

    async def refresh_token(self,
                            response: Response,
                            refresh_token: str
                            ) -> dict:
        """
                Refreshes tokens by generating new access and refresh tokens and setting cookies.

                Args:
                    response (Response): The response object to set cookies.
                    refresh_token (str): The current refresh token.

                Returns:
                    dict: A dictionary containing the new access and refresh tokens.
                """

        username = self.decode_token(refresh_token, settings.refresh_secret)
        new_access_token = self.create_access_token(data={"sub": username})
        new_refresh_token = self.create_refresh_token(data={"sub": username})

        response.set_cookie(key="access_token",
                            value=new_access_token,
                            httponly=True)
        response.set_cookie(key="refresh_token",
                            value=new_refresh_token,
                            httponly=True)

        return {"access_token": new_access_token,
                "refresh_token": new_refresh_token}

    def get_current_user(self, request: Request) -> str:
        """
                Retrieves the current user from the access token in cookies.

                Args:
                    request (Request): The request object containing cookies.

                Returns:
                    str: The username of the current user.

                Raises:
                    HTTPException: If the user is not authenticated.
                """
        token = request.cookies.get("access_token")
        if not token:
            raise HTTPException(status_code=401,
                                detail="Not authenticated")
        return self.decode_token(token, settings.secret)

    async def is_admin(self, request: Request,
                       db: AsyncSession
                       ) -> UserModel:
        """
                Verifies if the current user is an admin.

                Args:
                    request (Request): The request object containing cookies.
                    db (AsyncSession): The database session.

                Returns:
                    UserModel: The user model if the user is an admin.

                Raises:
                    HTTPException: If the user is not authenticated or lacks admin privileges.
                """
        token = request.cookies.get("access_token")
        if not token:
            raise HTTPException(status_code=401,
                                detail="Not authenticated")

        username = self.decode_token(token, settings.secret)
        result = await db.execute(select(UserModel).where(UserModel.username == username))
        user = result.scalar()
        if not user or not user.is_admin:
            raise HTTPException(status_code=403, detail="Not enough privileges")
        return user

    async def logout(self, response: Response):
        """
                Logs out the user by deleting the authentication cookies.

                Args:
                    response (Response): The response object to delete cookies.

                Returns:
                    dict: A message confirming successful logout.
                """

        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")

        return {"detail": "Logged out successfully"}
