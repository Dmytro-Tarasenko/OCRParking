from typing import Annotated

from fastapi import Request, Response, Depends
from fastapi.routing import APIRouter
from fastapi.responses import HTMLResponse

from frontend.routes import templates

router = APIRouter(prefix='/user',
                   default_response_class=HTMLResponse,
                   include_in_schema=False)


@router.get('/')
def get_user_page(request: Request):
    return templates.TemplateResponse('user/user.html',
                                      {'request': request})
