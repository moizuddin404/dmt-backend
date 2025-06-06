from fastapi import FastAPI
from fastapi.responses import JSONResponse
from .config import Config
from fastapi.middleware.cors import CORSMiddleware
from .routes import router

config = Config()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers= ["*"],
)

app.include_router(router, prefix="/file")

@app.get("/")
def home():
    return JSONResponse(status_code=200, content={"message": "Running with Passion"})

__all__ = ["config", "app"]