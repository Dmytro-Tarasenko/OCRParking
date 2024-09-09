import uvicorn
from fastapi import FastAPI

from routes.auth_routes import router as auth_router
# from admin.routes import router as admin_router

app = FastAPI()

app.include_router(auth_router)
# app.include_router(admin_router)


@app.get("/")
async def read_root():
    return {"message": "Welcome to OCRParking!"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
