import logging
import sys
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.routes import router
from app.infrastructure.sqlite_repository import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("payment_service.log"),
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("PaymentService starting up")
    await init_db()
    yield
    logger.info("PaymentService shutting down")


app = FastAPI(title="PaymentService", version="1.0.0", lifespan=lifespan)
app.include_router(router)


@app.get("/health")
async def health():
    logger.info("Health check called")
    return {"service": "PaymentService", "status": "ok"}
