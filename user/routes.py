from typing import Annotated, Any

from fastapi import Request, Response, Depends, Cookie
from fastapi.routing import APIRouter
from fastapi.responses import HTMLResponse

from frontend.routes import templates
from auth.auth import Authentication
from schemas.auth import User

auth = Authentication()

router = APIRouter(prefix='/user',
                   default_response_class=HTMLResponse,
                   include_in_schema=False)


@router.get('/')
def get_user_page(
    request: Request,
    access_token: Annotated[str | None, Cookie()] = None
) -> Any:
    user = None
    if access_token:
        username = auth.get_current_user(request)
        user = User(username=username)
    return templates.TemplateResponse('user/user.html',
                                      {'request': request,
                                       'user': user})
