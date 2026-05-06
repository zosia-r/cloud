import logging
import sys
import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.routes import router
from app.infrastructure.sqlite_repository import init_db
from app.infrastructure.consumer import start_consumer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("notification_service.log"),
    ]
)
logger = logging.getLogger(__name__)

_consumer_connection = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _consumer_connection
    logger.info("NotificationService starting up")
    await init_db()
    try:
        _consumer_connection = await start_consumer()
        logger.info("NotificationService consumer started successfully")
    except Exception as e:
        logger.error(f"Could not connect to RabbitMQ: {e}. Service will run without consumer.")
    yield
    logger.info("NotificationService shutting down")
    if _consumer_connection:
        await _consumer_connection.close()


app = FastAPI(title="NotificationService", version="1.0.0", lifespan=lifespan)
app.include_router(router)


@app.get("/health")
async def health():
    logger.info("Health check called")
    return {"service": "NotificationService", "status": "ok"}
