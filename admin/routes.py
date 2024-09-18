from datetime import timedelta, datetime

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Request, Cookie, Form, Response
from fastapi import HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload, selectinload

from settings import EnvSettings
from auth.auth import Authentication
from db_models.db import get_session
from schemas.auth import User
from db_models.orms import UserORM, ParkingHistoryORM, BillingORM, CarORM, TariffORM
from frontend.routes import templates

auth = Authentication()

settings = EnvSettings()

router = APIRouter(prefix='/admin',
                   default_response_class=HTMLResponse,
                   # include_in_schema=False,
                   tags=["Admin"])


@router.get("/", response_class=HTMLResponse)
async def get_admin_page(
        request: Request,
        db: AsyncSession = Depends(get_session),
        access_token: Annotated[str | None, Cookie()] = None
):
    """
        Get the admin page.

        This endpoint serves the admin page if the user is authenticated and has admin rights.
        If the user is not authenticated or doesn't have admin rights, an appropriate message
        or login page will be returned.

        Args:
            request (Request): The HTTP request object.
            db (AsyncSession): The database session dependency.
            access_token (Annotated[str | None, Cookie()]): The access token from cookies, if available.

        Returns:
            HTMLResponse:
                - Admin page template if the user is an admin.
                - Login form template if the user is not authenticated.
                - Access denied template if the user is not an admin.

        Raises:
            None
        """
    if not access_token:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    current_username = auth.get_current_user(request)

    result = await db.execute(select(UserORM).where(UserORM.username == current_username))
    user_db = result.scalar()

    if not user_db or not user_db.is_admin:
        return templates.TemplateResponse("admin/mistake.html", {"request": request, "message": "Access denied. "
                                                                                                "Admins only."})

    return templates.TemplateResponse("admin/admin.html", {"request": request, "user": user_db})


@router.get("/user_management", response_class=HTMLResponse, name="get_user_management")
async def get_user_management(request: Request, db: AsyncSession = Depends(get_session),
                              access_token: Annotated[str | None, Cookie()] = None):
    """
        Retrieves the user management page for admin users.

        If the user is not authenticated or does not have an admin role,
        they are redirected to the login page.

        Args:
            request (Request): The current request object.
            db (AsyncSession): The asynchronous database session, injected by FastAPI dependency.
            access_token (Annotated[str | None, Cookie]): The JWT access token stored in cookies. Defaults to None if not provided.

        Returns:
            HTMLResponse:
                - Returns the 'admin/user_management.html' template if the user is authenticated and has admin privileges.
                - Returns the 'auth/login_form.html' template if the user is not authenticated or lacks admin privileges.

        Raises:
            None
        """
    if not access_token:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    current_username = auth.get_current_user(request)
    res = await db.execute(select(UserORM).where(UserORM.username == current_username))
    current_user = res.scalar()

    if not current_user or not current_user.is_admin:
        return templates.TemplateResponse('auth/login_form.html',
                                          {'request': request, 'user': None, 'error': 'Admin access required'})

    user = User(username=current_user.username,
                is_admin=current_user.is_admin)

    return templates.TemplateResponse("admin/user_management.html", {"request": request,
                                                                     "user": user})


@router.get("/tariff_management", response_class=HTMLResponse, name="get_tariff_management")
async def get_tariff_management(request: Request, db: AsyncSession = Depends(get_session),
                                access_token: Annotated[str | None, Cookie()] = None):
    """
        Handles the GET request for the tariff management page.

        This route allows an admin user to access the tariff management page. If the user is not logged in
        or doesn't have admin privileges, they will be redirected to the login page.

        Args:
            request (Request): The request object containing details of the current request.
            db (AsyncSession): The asynchronous database session used to fetch the user data.
            access_token (str, optional): The access token stored in cookies to identify the logged-in user.

        Returns:
            TemplateResponse:
                - If the user is not logged in, returns the login form page.
                - If the user is logged in but not an admin, returns the login form page with an error message.
                - If the user is an admin, returns the tariff management page.

        Raises:
            None.
        """
    if not access_token:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    current_username = auth.get_current_user(request)
    res = await db.execute(select(UserORM).where(UserORM.username == current_username))
    current_user = res.scalar()

    if not current_user or not current_user.is_admin:
        return templates.TemplateResponse('auth/login_form.html',
                                          {'request': request, 'user': None, 'error': 'Admin access required'})

    user = User(username=current_user.username,
                is_admin=current_user.is_admin)

    return templates.TemplateResponse("admin/tariff_management.html", {"request": request,
                                                                       "user": user})


@router.get("/blacklist_management", response_class=HTMLResponse, name="get_blacklist_management")
async def get_blacklist_management(request: Request, access_token: Annotated[str | None, Cookie()] = None,
                                   db: AsyncSession = Depends(get_session)):
    """
        Renders the blacklist management page for an admin user.

        If no access token is provided, or if the current user is not an admin, the login form is rendered.
        Otherwise, the blacklist management page is returned.

        Args:
            request (Request): The incoming HTTP request object.
            access_token (str | None, optional): The access token from the user's cookie. Defaults to None.
            db (AsyncSession): The database session for querying user data. Defaults to an asynchronous session from `get_session`.

        Returns:
            TemplateResponse: The HTML response to render the appropriate template, either the login form or the blacklist management page.

        Raises:
            None
        """
    if not access_token:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    current_username = auth.get_current_user(request)
    res = await db.execute(select(UserORM).where(UserORM.username == current_username))
    current_user = res.scalar()

    if not current_user or not current_user.is_admin:
        return templates.TemplateResponse('auth/login_form.html',
                                          {'request': request, 'user': None, 'error': 'Admin access required'})

    user = User(username=current_user.username,
                is_admin=current_user.is_admin)

    return templates.TemplateResponse("admin/blacklist_management.html", {"request": request, "user": user})


@router.get("/stats_management", response_class=HTMLResponse, name="get_stats_management")
async def get_stats_management(request: Request, db: AsyncSession = Depends(get_session),
                               access_token: Annotated[str | None, Cookie()] = None):
    """
        Renders the admin statistics management page. If the user is not authenticated or is not an admin,
        they will be redirected to the login page or receive a 403 error.

        Args:
            request (Request): The incoming HTTP request object.
            db (AsyncSession, optional): The database session dependency for querying data.
            access_token (str | None, optional): The access token extracted from cookies to identify the user.

        Returns:
            TemplateResponse: The response with the rendered HTML page for stats management if the user is authorized.
            Otherwise, it returns the login page or raises a 403 HTTP exception if the user is unauthorized.

        Raises:
            HTTPException: If the user is not an admin or if authorization fails.
        """
    if not access_token:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    current_username = auth.get_current_user(request)
    res = await db.execute(select(UserORM).where(UserORM.username == current_username))
    current_user = res.scalar()

    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    cars = await db.execute(select(CarORM))
    cars_list = cars.scalars().all()

    user = User(username=current_user.username,
                is_admin=current_user.is_admin)

    return templates.TemplateResponse("admin/stats_management.html", {
        "request": request,
        "cars": cars_list,
        "user": user
    })


@router.get("/user_list", response_class=HTMLResponse, name="get_user_list")
async def get_user_list(request: Request, db: AsyncSession = Depends(get_session),
                        access_token: Annotated[str | None, Cookie()] = None):
    """
        Retrieve and display a list of users.

        This route fetches a list of all users from the database and renders it
        in the 'user_list.html' template. If the user is not authenticated,
        they are redirected to the login page.

        Args:
            request (Request): The HTTP request object.
            db (AsyncSession): An asynchronous session for interacting with the database.
            access_token (str | None): A cookie containing the user's access token (optional).

        Returns:
            TemplateResponse: Renders the 'user_list.html' template with the list of users
            or redirects to the login page if the user is not authenticated.
        """
    if not access_token:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    users = await db.execute(select(UserORM))
    user_list = users.scalars().all()

    return templates.TemplateResponse("admin/user_list.html", {"request": request, "users": user_list})


@router.get("/add_user", response_class=HTMLResponse)
async def add_user_form(request: Request, db: AsyncSession = Depends(get_session),
                        access_token: Annotated[str | None, Cookie()] = None):
    """
        Display the 'Add User' form.

        This route allows administrators to view the 'Add User' form.
        Non-authenticated users or non-admin users are redirected to the login page.

        Args:
            request (Request): The HTTP request object.
            db (AsyncSession): An asynchronous session for interacting with the database.
            access_token (str | None): A cookie containing the user's access token (optional).

        Returns:
            TemplateResponse: Renders the 'add_user_form.html' template or redirects to
            the login page if the user is not authenticated or not an admin.
        """
    if not access_token:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    current_username = auth.get_current_user(request)
    res = await db.execute(select(UserORM).where(UserORM.username == current_username))
    current_user = res.scalar()

    if not current_user or not current_user.is_admin:
        return templates.TemplateResponse('auth/login_form.html',
                                          {'request': request, 'user': None, 'error': 'Admin access required'})

    return templates.TemplateResponse("admin/add_user_form.html", {"request": request})


@router.post("/add_user", response_class=HTMLResponse)
async def add_user(
        request: Request,
        username: str = Form(...),
        email: str = Form(...),
        password: str = Form(...),
        db: AsyncSession = Depends(get_session),
        access_token: Annotated[str | None, Cookie()] = None
):
    """
        Handle the 'Add User' form submission.

        This route allows an admin to add a new user to the database. If the user
        is not authenticated, or not an admin, they are redirected to the login page.
        It ensures the username is unique and stores the user's details with a hashed password.

        Args:
            request (Request): The HTTP request object.
            username (str): The new user's username.
            email (str): The new user's email.
            password (str): The new user's password.
            db (AsyncSession): An asynchronous session for interacting with the database.
            access_token (str | None): A cookie containing the user's access token (optional).

        Returns:
            TemplateResponse: Renders the 'user_added.html' template after successful addition,
            or the 'add_user_form.html' template with an error message if any checks fail.
        """
    if not access_token:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    current_username = auth.get_current_user(request)

    res = await db.execute(select(UserORM).where(UserORM.username == current_username))
    current_user = res.scalar()

    if not current_user or not current_user.is_admin:
        return templates.TemplateResponse('auth/login_form.html',
                                          {'request': request, 'error': 'Admin access required'})

    existing_user = await db.execute(select(UserORM).where(UserORM.username == username))

    if existing_user.scalar():
        return templates.TemplateResponse("admin/add_user_form.html", {
            "request": request,
            "error": "Username already registered."
        })

    hashed_password = auth.get_password_hash(password)
    new_user = UserORM(username=username, email=email, password=hashed_password)

    db.add(new_user)
    await db.commit()

    return templates.TemplateResponse("admin/user_added.html", {"request": request, "username": username})


@router.post("/delete_user", response_class=HTMLResponse)
async def delete_user(request: Request, username: str = Form(...), db: AsyncSession = Depends(get_session),
                      access_token: Annotated[str | None, Cookie()] = None):
    """
       Delete a user by username.

       This route allows an admin to delete a user from the database. If the user is
       not authenticated or not an admin, they are redirected to the login page.
       If the user does not exist, an error is shown.

       Args:
           request (Request): The HTTP request object.
           username (str): The username of the user to be deleted.
           db (AsyncSession): An asynchronous session for interacting with the database.
           access_token (str | None): A cookie containing the user's access token (optional).

       Returns:
           TemplateResponse: Renders the 'user_deleted.html' template after successful deletion,
           or the 'delete_user_form.html' template with an error message if any checks fail.
       """
    user = None
    if access_token:
        current_username = auth.get_current_user(request)
        user = await db.execute(select(UserORM).where(UserORM.username == current_username))
        user = user.scalar()

    if user is None or not user.is_admin:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': user})

    result = await db.execute(select(UserORM).where(UserORM.username == username))
    deleted_user = result.scalar()

    if not deleted_user:
        return templates.TemplateResponse("admin/delete_user_form.html", {
            "request": request,
            "error": "User not found."
        })

    await db.delete(deleted_user)
    await db.commit()

    return templates.TemplateResponse("admin/user_deleted.html", {"request": request, "username": username})


@router.get("/banned_users", response_class=HTMLResponse, name="get_banned_users")
async def get_banned_users(request: Request, db: AsyncSession = Depends(get_session),
                           access_token: Annotated[str | None, Cookie()] = None):
    """
       Retrieves the list of banned users from the database and renders the banned users list.

       Args:
           request (Request): The FastAPI request object.
           db (AsyncSession): The asynchronous database session, retrieved via dependency injection.
           access_token (Optional[str]): The access token stored in the browser's cookie.

       Returns:
           HTMLResponse: Renders the 'banned_users_list.html' template with the banned users list,
                         or redirects to the login form if the user is not authenticated.
       """
    user = None
    if access_token:
        username = auth.get_current_user(request)
        user = User(username=username)

    if user is None:
        return templates.TemplateResponse('auth/login_form.html',
                                          {'request': request,
                                           'user': user})

    users = await db.execute(select(UserORM).where(UserORM.is_banned == True))
    banned_users = users.scalars().all()

    return templates.TemplateResponse("admin/banned_users_list.html",
                                      {"request": request, "banned_users": banned_users})


@router.post("/ban_user", response_class=HTMLResponse)
async def ban_user(
        request: Request,
        username: str = Form(...),
        db: AsyncSession = Depends(get_session),
        access_token: Annotated[Optional[str], Cookie()] = None
):
    """
        Bans a user by setting their 'is_banned' flag to True in the database.

        Args:
            request (Request): The FastAPI request object.
            username (str): The username of the user to ban.
            db (AsyncSession): The asynchronous database session, retrieved via dependency injection.
            access_token (Optional[str]): The access token stored in the browser's cookie.

        Returns:
            HTMLResponse: Renders a success page if the user is banned successfully,
                          or an appropriate error page if there are issues (e.g., user not found).

        Raises:
            HTTPException: If the user is not authorized or user to ban is not found.
        """
    if not access_token:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    current_username = auth.get_current_user(request)

    res = await db.execute(select(UserORM).where(UserORM.username == current_username))
    current_user = res.scalar()

    if not current_user:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to ban users")

    res = await db.execute(select(UserORM).where(UserORM.username == username))
    banned_user = res.scalar()

    if not banned_user:
        raise HTTPException(status_code=404, detail="User not found")

    if banned_user.is_banned:
        return templates.TemplateResponse("admin/ban_user_form.html", {
            "request": request,
            "msg": f"User {banned_user.username} is already banned"
        })

    banned_user.is_banned = True
    await db.commit()

    return templates.TemplateResponse("admin/ban_success.html", {
        "request": request,
        "msg": f"User {banned_user.username} banned successfully"
    })


@router.post("/unban_user", response_class=HTMLResponse)
async def unban_user(
        request: Request,
        username: str = Form(...),
        db: AsyncSession = Depends(get_session),
        access_token: Annotated[Optional[str], Cookie()] = None
):
    """
       Unbans a user by setting their 'is_banned' flag to False in the database.

       Args:
           request (Request): The FastAPI request object.
           username (str): The username of the user to unban.
           db (AsyncSession): The asynchronous database session, retrieved via dependency injection.
           access_token (Optional[str]): The access token stored in the browser's cookie.

       Returns:
           HTMLResponse: Renders a success page if the user is unbanned successfully,
                         or an appropriate error page if there are issues (e.g., user not found).

       Raises:
           HTTPException: If the user is not authorized or user to unban is not found.
       """
    if not access_token:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    current_username = auth.get_current_user(request)

    res = await db.execute(select(UserORM).where(UserORM.username == current_username))
    current_user = res.scalar()

    if not current_user:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to unban users")

    res = await db.execute(select(UserORM).where(UserORM.username == username))
    user = res.scalar()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.is_banned:
        return templates.TemplateResponse("admin/unban_user_form.html", {
            "request": request,
            "msg": f"User {user.username} is not banned"
        })

    user.is_banned = False
    await db.commit()

    return templates.TemplateResponse("admin/unban_success.html", {
        "request": request,
        "msg": f"User {user.username} unbanned successfully"
    })


@router.get("/tariffs", response_class=HTMLResponse)
async def list_tariffs(request: Request, db: AsyncSession = Depends(get_session),
                       access_token: Annotated[Optional[str], Cookie()] = None):
    """
        Displays the list of parking tariffs for administrators. If the user is not logged in
        or lacks administrative privileges, they are redirected to the login page or
        receive a '403 Forbidden' error.

        Args:
            request (Request): The current request object.
            db (AsyncSession): The asynchronous database session dependency.
            access_token (Optional[str], optional): The access token stored in cookies.

        Returns:
            TemplateResponse: Renders the tariff management page for admins, or the login page
            if access is not granted.

        Raises:
            HTTPException: If the current user is not an admin.
        """
    if not access_token:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    current_username = auth.get_current_user(request)

    res = await db.execute(select(UserORM).where(UserORM.username == current_username))
    current_user = res.scalar()

    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to set parking tariff")

    result = await db.execute(select(TariffORM).order_by(TariffORM.set_date.desc()).limit(1))
    current_tariff = result.scalar()

    all_tariffs = await db.execute(select(TariffORM).order_by(TariffORM.set_date.desc()))
    tariffs = all_tariffs.scalars().all()

    return templates.TemplateResponse("admin/tariff_management.html", {
        "request": request,
        "current_tariff": current_tariff,
        "tariffs": tariffs
    })


@router.post("/tariffs/add", response_class=HTMLResponse)
async def add_tariff(
        request: Request,
        new_rate: float = Form(...),
        db: AsyncSession = Depends(get_session),
        access_token: Annotated[Optional[str], Cookie()] = None
):
    """
        Adds a new parking tariff to the database. Only administrators are allowed to perform this action.

        Args:
            request (Request): The current request object.
            new_rate (float): The new tariff rate to be added.
            db (AsyncSession): The asynchronous database session dependency.
            access_token (Optional[str], optional): The access token stored in cookies.

        Returns:
            TemplateResponse: Renders the tariff added confirmation page, or the login page
            if access is not granted.

        Raises:
            HTTPException: If the current user is not an admin.
        """
    if not access_token:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    current_username = auth.get_current_user(request)

    res = await db.execute(select(UserORM).where(UserORM.username == current_username))
    current_user = res.scalar()

    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to set parking tariff")

    new_tariff = TariffORM(tariff=new_rate, set_date=datetime.today().date())

    db.add(new_tariff)
    await db.commit()

    return templates.TemplateResponse("admin/tariff_added.html", {
        "request": request,
        "msg": f"Parking tariff set to {new_rate} successfully"
    })


@router.get("/get_last_tariff", response_class=HTMLResponse)
async def get_last_tariff(request: Request, db: AsyncSession = Depends(get_session),
                          access_token: Annotated[Optional[str], Cookie()] = None):
    """
        Retrieves and displays the most recent parking tariff. Only administrators can access this route.

        Args:
            request (Request): The current request object.
            db (AsyncSession): The asynchronous database session dependency.
            access_token (Optional[str], optional): The access token stored in cookies.

        Returns:
            TemplateResponse: Renders the page with the last tariff information or the login page
            if access is not granted.

        Raises:
            HTTPException: If the current user is not an admin.
        """
    if not access_token:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    current_username = auth.get_current_user(request)

    res = await db.execute(select(UserORM).where(UserORM.username == current_username))
    current_user = res.scalar()

    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to set parking tariff")

    last_tariff = await db.execute(select(TariffORM).order_by(TariffORM.set_date.desc(), TariffORM.id.desc()).limit(1))
    tariff = last_tariff.scalar()
    if tariff:
        print(f"Тариф: {tariff.tariff}, Дата встановлення: {tariff.set_date}")
    else:
        print("Тариф не знайдено")

    return templates.TemplateResponse("admin/_last_tariff.html", {
        "request": request,
        "tariff": tariff
    })


@router.get("/logout", response_class=HTMLResponse)
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_session),
                 access_token: Annotated[Optional[str], Cookie()] = None):
    """
        Logs out the current user by deleting their access and refresh tokens from cookies. Only
        administrators can perform this action.

        Args:
            request (Request): The current request object.
            response (Response): The response object to manipulate cookies.
            db (AsyncSession): The asynchronous database session dependency.
            access_token (Optional[str], optional): The access token stored in cookies.

        Returns:
            TemplateResponse: Renders the logout success page or the login page if access is not granted.

        Raises:
            HTTPException: If the current user is not an admin.
        """
    if not access_token:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    current_username = auth.get_current_user(request)

    res = await db.execute(select(UserORM).where(UserORM.username == current_username))
    current_user = res.scalar()

    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to logout from admin panel")

    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")

    return templates.TemplateResponse("admin/logout_success.html", {"request": request})


@router.get("/user_selection", response_class=HTMLResponse, name="user_selection")
async def user_selection(request: Request, db: AsyncSession = Depends(get_session),
                         access_token: Annotated[Optional[str], Cookie()] = None):
    """
        Renders the user selection page for administrators.

        Args:
            request (Request): The current request object.
            db (AsyncSession): The database session for querying user data.
            access_token (Optional[str]): The access token for user authentication.

        Returns:
            HTMLResponse: Renders the user selection page or login page if not authenticated.

        Raises:
            HTTPException: If the user is not found in the database.
        """
    if not access_token:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    current_username = auth.get_current_user(request)
    res = await db.execute(
        select(UserORM).options(joinedload(UserORM.cars)).where(UserORM.username == current_username)
    )
    user = res.scalar()

    if not user:
        return templates.TemplateResponse('mistake.html', {"request": request, "message": "User not found"})

    users_res = await db.execute(select(UserORM).options(joinedload(UserORM.cars)))
    users = users_res.unique().scalars().all()

    return templates.TemplateResponse("admin/user_selection.html", {
        "request": request,
        "users": users
    })


@router.get("/user_stats", response_class=HTMLResponse, name="get_user_stats")
async def get_user_stats(request: Request, username: str, db: AsyncSession = Depends(get_session),
                         access_token: Annotated[Optional[str], Cookie()] = None):
    """
        Renders user statistics based on the given username.

        Args:
            request (Request): The current request object.
            username (str): The username of the user whose statistics will be displayed.
            db (AsyncSession): The database session for querying user and parking history data.
            access_token (Optional[str]): The access token for user authentication.

        Returns:
            HTMLResponse: Renders the user statistics page or login page if not authenticated.

        Raises:
            HTTPException: If the user is not found in the database.
        """
    if not access_token:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    res = await db.execute(
        select(UserORM).options(joinedload(UserORM.cars)).where(UserORM.username == username)
    )
    user = res.scalar()

    if not user:
        return templates.TemplateResponse('mistake.html', {"request": request, "message": "User not found"})

    parking_history = await db.execute(
        select(ParkingHistoryORM)
        .options(joinedload(ParkingHistoryORM.bill))
        .where(ParkingHistoryORM.car_id.in_(
            select(CarORM.id).where(CarORM.user_id == user.id)
        ))
    )
    history = parking_history.scalars().all()

    return templates.TemplateResponse("admin/user_stats.html", {
        "request": request,
        "user": user,
        "parking_history": history
    })


@router.get("/car_selection", response_class=HTMLResponse, name="car_selection")
async def car_selection(request: Request, db: AsyncSession = Depends(get_session),
                        access_token: Annotated[Optional[str], Cookie()] = None):
    """
        Renders the car selection page for administrators.

        Args:
            request (Request): The current request object.
            db (AsyncSession): The database session for querying car data.
            access_token (Optional[str]): The access token for user authentication.

        Returns:
            HTMLResponse: Renders the car selection page or login page if not authenticated.

        Raises:
            HTTPException: If the user is not authorized to access the page.
        """
    if not access_token:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    current_username = auth.get_current_user(request)
    res = await db.execute(select(UserORM).where(UserORM.username == current_username))
    current_user = res.scalar()

    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access car selection")

    cars = await db.execute(select(CarORM))
    cars = cars.scalars().all()

    return templates.TemplateResponse("admin/car_selection.html", {
        "request": request,
        "cars": cars
    })


@router.get("/car_stats/{car_id}", response_class=HTMLResponse, name="get_car_stats")
async def get_car_stats(request: Request, car_id: int, db: AsyncSession = Depends(get_session),
                        access_token: Annotated[Optional[str], Cookie()] = None):
    """
        Renders the statistics of a car based on the given car ID.

        Args:
            request (Request): The current request object.
            car_id (int): The ID of the car whose statistics will be displayed.
            db (AsyncSession): The database session for querying car and parking history data.
            access_token (Optional[str]): The access token for user authentication.

        Returns:
            HTMLResponse: Renders the car statistics page or login page if not authenticated.

        Raises:
            HTTPException: If the user is not authorized or the car is not found.
        """
    if not access_token:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    current_username = auth.get_current_user(request)
    res = await db.execute(select(UserORM).where(UserORM.username == current_username))
    current_user = res.scalar()

    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to look car statistics")

    car = await db.execute(select(CarORM).options(selectinload(CarORM.parking_history)).where(CarORM.id == car_id))
    car = car.scalar()

    if not car:
        return templates.TemplateResponse('mistake.html', {"request": request, "message": "Car not found"})

    parking_history = await db.execute(
        select(ParkingHistoryORM)
        .options(joinedload(ParkingHistoryORM.bill))
        .where(ParkingHistoryORM.car_id == car_id)
    )
    history = parking_history.scalars().all()

    user = User(username=current_user.username,
                is_admin=current_user.is_admin)

    return templates.TemplateResponse("admin/car_stats.html", {
        "request": request,
        "car_plate": car.car_plate,
        "parking_history": history,
        "user": user
    })


@router.get("/parking_stats", response_class=HTMLResponse, name="get_parking_stats")
async def get_parking_stats(request: Request, access_token: Annotated[Optional[str], Cookie()] = None,
                            db: AsyncSession = Depends(get_session)):
    """
        Renders overall parking statistics for administrators.

        Args:
            request (Request): The current request object.
            access_token (Optional[str]): The access token for user authentication.
            db (AsyncSession): The database session for querying parking and billing data.

        Returns:
            HTMLResponse: Renders the parking statistics page or login page if not authenticated.

        Raises:
            HTTPException: If the user is not authorized to view parking statistics.
        """
    if not access_token:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    current_username = auth.get_current_user(request)
    res = await db.execute(select(UserORM).where(UserORM.username == current_username))
    current_user = res.scalar()

    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to look parking statistics")

    total_parkings_count = await db.scalar(select(func.count(ParkingHistoryORM.id)))

    total_cost = await db.execute(select(BillingORM.cost))
    total_earned = sum(bill for bill in total_cost.scalars())

    return templates.TemplateResponse("admin/parking_stats.html", {
        "request": request,
        "total_parkings": total_parkings_count,
        "total_earned": total_earned
    })


@router.get("/active_users_stats", response_class=HTMLResponse, name="get_active_users_stats")
async def get_active_users_stats(request: Request, access_token: Annotated[Optional[str], Cookie()] = None,
                                 db: AsyncSession = Depends(get_session)):
    """
        Get the statistics of active users in the last 30 days.

        Args:
            request (Request): The request object.
            access_token (Optional[str]): Access token stored in cookies, used for authentication.
            db (AsyncSession): The database session, passed as a dependency.

        Returns:
            HTMLResponse: Renders the template with active user statistics.

        Raises:
            HTTPException: If the user is not authorized or is not an admin.
        """
    if not access_token:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    current_username = auth.get_current_user(request)
    res = await db.execute(select(UserORM).where(UserORM.username == current_username))
    current_user = res.scalar()

    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to view user statistics")

    last_month = datetime.now() - timedelta(days=30)

    active_users = await db.execute(
        select(func.count(UserORM.id))
        .select_from(ParkingHistoryORM)
        .join(UserORM, ParkingHistoryORM.car_id == UserORM.id)
        .where(ParkingHistoryORM.start_time >= last_month)
    )

    count_active_users = active_users.scalar()

    return templates.TemplateResponse("admin/active_users_stats.html", {
        "request": request,
        "active_users_count": count_active_users
    })


@router.get("/banned_users_stats", response_class=HTMLResponse, name="get_banned_users_stats")
async def get_banned_users_stats(request: Request, access_token: Annotated[Optional[str], Cookie()] = None,
                                 db: AsyncSession = Depends(get_session)):
    """
        Get the statistics of banned users.

        Args:
            request (Request): The request object.
            access_token (Optional[str]): Access token stored in cookies, used for authentication.
            db (AsyncSession): The database session, passed as a dependency.

        Returns:
            HTMLResponse: Renders the template with banned user statistics.

        Raises:
            HTTPException: If the user is not authorized or is not an admin.
        """
    if not access_token:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    current_username = auth.get_current_user(request)
    res = await db.execute(select(UserORM).where(UserORM.username == current_username))
    current_user = res.scalar()

    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to look user statistics")
    banned_users = await db.execute(
        select(func.count(UserORM.id)).where(UserORM.is_banned == True)
    )
    count_banned_users = banned_users.scalar()

    return templates.TemplateResponse("admin/banned_users_stats.html", {
        "request": request,
        "banned_users_count": count_banned_users
    })


@router.get("/parking_occupancy_stats", response_class=HTMLResponse, name="get_parking_occupancy_stats")
async def get_parking_occupancy_stats(request: Request, access_token: Annotated[Optional[str], Cookie()] = None,
                                      db: AsyncSession = Depends(get_session), period: str = "week"):
    """
        Get parking occupancy statistics for a given period.

        Args:
            request (Request): The request object.
            access_token (Optional[str]): Access token stored in cookies, used for authentication.
            db (AsyncSession): The database session, passed as a dependency.
            period (str): The time period for occupancy stats ("week", "month", or "day").

        Returns:
            HTMLResponse: Renders the template with parking occupancy statistics.

        Raises:
            HTTPException: If the user is not authorized or is not an admin.
        """
    if not access_token:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    current_username = auth.get_current_user(request)
    res = await db.execute(select(UserORM).where(UserORM.username == current_username))
    current_user = res.scalar()

    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to look parking statistics")

    now = datetime.now()

    if period == "week":
        start_time = now - timedelta(weeks=1)
    elif period == "month":
        start_time = now - timedelta(days=30)
    else:
        start_time = now - timedelta(days=1)

    total_parkings = await db.execute(
        select(func.count(ParkingHistoryORM.id)).where(ParkingHistoryORM.start_time >= start_time)
    )
    total_parkings_count = total_parkings.scalar()

    average_occupancy = (total_parkings_count / (settings.total_spots * 24)) * 100

    return templates.TemplateResponse("admin/parking_occupancy_stats.html", {
        "request": request,
        "average_occupancy_percent": average_occupancy,
        "period": period
    })


@router.get("/max_cars_day_stats", response_class=HTMLResponse, name="get_max_cars_day_stats")
async def get_max_cars_per_day_stats(request: Request, access_token: Annotated[Optional[str], Cookie()] = None,
                                     db: AsyncSession = Depends(get_session)):
    """
        Get the maximum number of cars parked in a single day.

        Args:
            request (Request): The request object.
            access_token (Optional[str]): Access token stored in cookies, used for authentication.
            db (AsyncSession): The database session, passed as a dependency.

        Returns:
            HTMLResponse: Renders the template with max cars parked per day statistics.

        Raises:
            HTTPException: If the user is not authorized or is not an admin.
        """
    if not access_token:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    current_username = auth.get_current_user(request)
    res = await db.execute(select(UserORM).where(UserORM.username == current_username))
    current_user = res.scalar()

    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to look cars statistics")
    max_cars = await db.execute(
        select(func.count(ParkingHistoryORM.id)).group_by(func.date(ParkingHistoryORM.start_time))
    )
    max_cars_per_day = max_cars.scalar()

    return templates.TemplateResponse("admin/max_cars_day_stats.html", {
        "request": request,
        "max_cars_in_a_day": max_cars_per_day
    })


@router.get("/peak_activity_time_stats", response_class=HTMLResponse, name="get_peak_activity_time_stats")
async def get_peak_activity_time_stats(request: Request, access_token: Annotated[Optional[str], Cookie()] = None,
                                       db: AsyncSession = Depends(get_session)):
    """
       Get statistics on the peak parking activity time.

       Args:
           request (Request): The current HTTP request object.
           access_token (str, optional): JWT access token stored in cookies.
           db (AsyncSession): Database session for executing queries.

       Returns:
           TemplateResponse: Renders the template for peak activity time statistics.

       Raises:
           HTTPException: If the user is not authenticated or not an admin.
       """
    if not access_token:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    current_username = auth.get_current_user(request)
    res = await db.execute(select(UserORM).where(UserORM.username == current_username))
    current_user = res.scalar()

    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to look statistics")
    peak_time = await db.execute(
        select(func.extract('hour', ParkingHistoryORM.start_time), func.count(ParkingHistoryORM.id))
        .group_by(func.extract('hour', ParkingHistoryORM.start_time))
        .order_by(func.count(ParkingHistoryORM.id).desc())
    )
    most_active_hour, count = peak_time.first()

    return templates.TemplateResponse("admin/peak_activity_time_stats.html", {
        "request": request,
        "most_active_hour": most_active_hour,
        "parking_count": count
    })


@router.get("/average_parking_duration_stats", response_class=HTMLResponse, name="get_average_parking_duration_stats")
async def get_average_parking_duration_stats(request: Request, access_token: Annotated[Optional[str], Cookie()] = None,
                                             db: AsyncSession = Depends(get_session)):
    """
        Get statistics on the average parking duration.

        Args:
            request (Request): The current HTTP request object.
            access_token (str, optional): JWT access token stored in cookies.
            db (AsyncSession): Database session for executing queries.

        Returns:
            TemplateResponse: Renders the template for average parking duration statistics.

        Raises:
            HTTPException: If the user is not authenticated or not an admin.
        """
    if not access_token:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    current_username = auth.get_current_user(request)
    res = await db.execute(select(UserORM).where(UserORM.username == current_username))
    current_user = res.scalar()

    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to look statistics")
    average_duration = await db.execute(
        select(func.avg(func.extract('epoch', ParkingHistoryORM.end_time - ParkingHistoryORM.start_time)))
        .where(ParkingHistoryORM.end_time.isnot(None))
    )
    average_duration_seconds = average_duration.scalar()

    average_duration_hours = average_duration_seconds / 3600 if average_duration_seconds else 0

    return templates.TemplateResponse("admin/average_parking_duration_stats.html", {
        "request": request,
        "average_parking_duration_hours": average_duration_hours
    })


@router.get("/parking_count_stats", response_class=HTMLResponse, name="get_parking_count_stats")
async def get_parking_count_stats(request: Request, access_token: Annotated[Optional[str], Cookie()] = None,
                                  db: AsyncSession = Depends(get_session), period: str = "week"):
    """
        Get parking count statistics based on the specified time period.

        Args:
            request (Request): The current HTTP request object.
            access_token (str, optional): JWT access token stored in cookies.
            db (AsyncSession): Database session for executing queries.
            period (str): Time period for which statistics are calculated ('day', 'week', or 'month').

        Returns:
            TemplateResponse: Renders the template for parking count statistics.

        Raises:
            HTTPException: If the user is not authenticated or not an admin.
        """
    if not access_token:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    current_username = auth.get_current_user(request)
    res = await db.execute(select(UserORM).where(UserORM.username == current_username))
    current_user = res.scalar()

    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to look parking statistics")
    now = datetime.now()

    if period == "week":
        start_time = now - timedelta(weeks=1)
    elif period == "month":
        start_time = now - timedelta(days=30)
    else:
        start_time = now - timedelta(days=1)

    parking_count = await db.execute(
        select(func.count(ParkingHistoryORM.id)).where(ParkingHistoryORM.start_time >= start_time)
    )
    count = parking_count.scalar()

    return templates.TemplateResponse("admin/parking_count_stats.html", {
        "request": request,
        "parking_count": count,
        "period": period
    })


@router.get("/available_spots_stats", response_class=HTMLResponse, name="get_available_spots_stats")
async def get_available_spots_stats(request: Request, access_token: Annotated[Optional[str], Cookie()] = None,
                                    db: AsyncSession = Depends(get_session)):
    """
        Get statistics on available parking spots.

        Args:
            request (Request): The current HTTP request object.
            access_token (str, optional): JWT access token stored in cookies.
            db (AsyncSession): Database session for executing queries.

        Returns:
            TemplateResponse: Renders the template for available parking spot statistics.

        Raises:
            HTTPException: If the user is not authenticated or not an admin.
        """
    if not access_token:
        return templates.TemplateResponse('auth/login_form.html', {'request': request, 'user': None})

    current_username = auth.get_current_user(request)
    res = await db.execute(select(UserORM).where(UserORM.username == current_username))
    current_user = res.scalar()

    if not current_user or not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to look parking statistics")
    occupied_spots = await db.execute(
        select(func.count(ParkingHistoryORM.id)).where(ParkingHistoryORM.end_time.is_(None))
    )
    occupied_spots_count = occupied_spots.scalar()

    available_spots = settings.total_spots - occupied_spots_count

    return templates.TemplateResponse("admin/available_spots_stats.html", {
        "request": request,
        "available_spots": available_spots
    })
