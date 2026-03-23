from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.games import router as games_router
from app.api.routes.health import router as health_router
from app.config import settings
from app.dependencies import katago_engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        katago_engine.start()
    except Exception:
        pass
    yield
    try:
        katago_engine.stop()
    except Exception:
        pass


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router)
app.include_router(games_router)
