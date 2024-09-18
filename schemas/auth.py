from pydantic import BaseModel, EmailStr
from typing import Optional


class Token(BaseModel):
    """
        Represents the token model containing access and refresh tokens.

        Attributes:
            access_token (str): The JWT access token for user authentication.
            refresh_token (str): The JWT refresh token used for renewing the access token.
        """
    access_token: str
    refresh_token: str


class TokenData(BaseModel):
    """
        Represents data associated with a token, such as the username.

        Attributes:
            username (Optional[str]): The username associated with the token, default is None.
        """
    username: str | None = None


class User(BaseModel):
    """
        Represents a user in the system.

        Attributes:
            username (str): The username of the user.
            email (Optional[str]): The email address of the user, default is None.
            is_admin (bool): Whether the user has admin privileges, default is False.
            is_banned (bool): Whether the user is banned from the system, default is False.
        """
    username: str
    email: Optional[str] = None
    is_admin: bool = False
    is_banned: bool = False


class UserInDB(User):
    """
        Represents a user stored in the database, with the hashed password.

        Attributes:
            hashed_password (str): The hashed password of the user.
        """
    hashed_password: str


class UserCreate(BaseModel):
    """
        Represents the data required to create a new user.

        Attributes:
            username (str): The username of the new user.
            email (EmailStr): The email address of the new user.
            password (str): The password of the new user.
        """
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """
        Represents the data required for a user to log in.

        Attributes:
            username (str): The username of the user.
            password (str): The password of the user.
        """
    username: str
    password: str
