import logging
import sys
import os
import asyncio
from dotenv import load_dotenv

# Załaduj .env PRZED innymi importami
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("notification_service.log")]
)
logger = logging.getLogger(__name__)
logger.info(f"Loading .env from: {env_path}")

from app.api.routes import router
from app.infrastructure.dynamodb_repository import init_db
from app.infrastructure.rabbitmq import start_consumer

_consumer_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _consumer_task
    logger.info("NotificationService starting")
    try:
        await init_db()
        logger.info("NotificationService AWS DynamoDB connection initialized successfully")
    except Exception as e:
        logger.error(f"NotificationService failed to initialize AWS connection: {str(e)}", exc_info=True)
        raise
    
    try:
        # Start RabbitMQ consumer in background
        _consumer_task = asyncio.create_task(start_consumer())
        logger.info("RabbitMQ consumer started in background")
        await asyncio.sleep(0.5)  # Give consumer time to start
    except Exception as e:
        logger.error(f"Error starting consumer: {e}", exc_info=True)
    
    yield
    
    if _consumer_task:
        try:
            _consumer_task.cancel()
            await asyncio.wait_for(_consumer_task, timeout=2.0)
        except asyncio.CancelledError:
            pass
        except asyncio.TimeoutError:
            logger.warning("Timeout closing consumer")
        except Exception as e:
            logger.error(f"Error closing consumer: {e}")
    
    logger.info("NotificationService stopping")

app = FastAPI(title="NotificationService", version="2.0.0", lifespan=lifespan)
app.include_router(router)

@app.get("/health")
async def health():
    return {"service": "NotificationService", "status": "ok"}

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005, log_level="info")
