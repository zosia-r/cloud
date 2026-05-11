import logging
import sys
import os
from dotenv import load_dotenv

# Załaduj .env PRZED innymi importami
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.api.routes import router
from app.infrastructure.sqlite_repository import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info(f"Załaduję .env z: {env_path}")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("design_service.log")]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("DesignService uruchamianie")
    await init_db()
    yield
    logger.info("DesignService zatrzymywanie")


app = FastAPI(title="DesignService", version="2.0.0", lifespan=lifespan)
app.include_router(router)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "error": type(exc).__name__}
    )


@app.get("/health")
async def health():
    logger.info("Health check")
    return {"service": "DesignService", "status": "ok"}
