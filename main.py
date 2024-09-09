from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn

from routes.auth_routes import router as auth_router
from frontend.routes import router as front_router
from user.routes import router as user_router


app = FastAPI()

app.include_router(auth_router)
# app.include_router(admin_router)

static_path = Path(__file__).parent / 'frontend' / 'static'
app.mount("/static", StaticFiles(directory=static_path), name='static')

app.include_router(auth_router)
app.include_router(front_router)
app.include_router(user_router)


if __name__ == "__main__":
    uvicorn.run(app=app,
                host="localhost",
                port=8080)
