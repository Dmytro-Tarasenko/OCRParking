from fastapi.routing import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix='user',
                   default_response_class=HTMLResponse,
                   include_in_schema=False)


@router.get('/')
def get_user_page(request):
    pass
