import logging, sys, os
from dotenv import load_dotenv

# Załaduj .env PRZED innymi importami
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.api.routes import router
from app.infrastructure.rds_repository import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("inventory_service.log")]
)
logger = logging.getLogger(__name__)
logger.info(f"Loading .env from: {env_path}")


@asynccontextmanager
async def lifespan(app):
    logger.info("InventoryService starting")
    try:
        await init_db()
        logger.info("InventoryService AWS RDS connection initialized successfully")
    except Exception as e:
        logger.error(f"InventoryService failed to initialize AWS connection: {str(e)}", exc_info=True)
        raise
    yield
    logger.info("InventoryService stopping")

app = FastAPI(title="InventoryService", version="2.0.0", lifespan=lifespan)
app.include_router(router)

@app.get("/health")
async def health():
    return {"service": "InventoryService", "status": "ok"}

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "error": type(exc).__name__}
    )
