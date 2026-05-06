import logging, sys, os, asyncio
from dotenv import load_dotenv

# Załaduj .env PRZED innymi importami
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("notification_service.log")])
logger = logging.getLogger(__name__)

from app.api.routes import router
from app.infrastructure.sqlite_repository import init_db
from app.infrastructure.rabbitmq import start_consumer

_consumer_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _consumer_task
    logger.info("NotificationService uruchamianie")
    await init_db()
    try:
        # Uruchom consumer w tle (nie czekaj na jego zwrócenie)
        _consumer_task = asyncio.create_task(start_consumer())
        logger.info("Consumer RabbitMQ uruchomiony w tle")
        await asyncio.sleep(0.5)  # Daj consumerowi chwilę na start
    except Exception as e:
        logger.error(f"Błąd przy uruchamianiu consumera: {e}")
    yield
    if _consumer_task:
        try:
            _consumer_task.cancel()
            await asyncio.wait_for(_consumer_task, timeout=2.0)
        except asyncio.CancelledError:
            pass
        except asyncio.TimeoutError:
            logger.warning("Timeout przy zamykaniu consumera")
        except Exception as e:
            logger.error(f"Błąd zamykania consumera: {e}")

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
