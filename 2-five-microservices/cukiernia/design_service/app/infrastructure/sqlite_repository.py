import aiosqlite
import logging
from typing import List
from datetime import datetime
from app.domain.models import DesignFile
from app.domain.repository import DesignRepository

logger = logging.getLogger(__name__)
DB_PATH = "design_service.db"


async def init_db():
    logger.info("Initializing DesignService database")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS design_files (
                id TEXT PRIMARY KEY,
                order_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                extension TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        await db.commit()
    logger.info("DesignService database initialized")


class SQLiteDesignRepository(DesignRepository):

    async def save(self, design: DesignFile) -> DesignFile:
        logger.info(f"Saving design file id={design.id}, filename={design.filename}, ext={design.extension}")
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO design_files VALUES (?,?,?,?,?)",
                (design.id, design.order_id, design.filename,
                 design.extension, design.created_at.isoformat())
            )
            await db.commit()
        logger.info(f"Design file id={design.id} saved to database")
        return design

    async def find_by_order_id(self, order_id: str) -> List[DesignFile]:
        logger.info(f"Fetching design files for order_id={order_id}")
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM design_files WHERE order_id=?", (order_id,)
            )
            rows = await cursor.fetchall()
        return [_row_to_design(r) for r in rows]

    async def find_all(self) -> List[DesignFile]:
        logger.info("Fetching all design files")
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM design_files ORDER BY created_at DESC")
            rows = await cursor.fetchall()
        return [_row_to_design(r) for r in rows]


def _row_to_design(row) -> DesignFile:
    return DesignFile(
        id=row["id"],
        order_id=row["order_id"],
        filename=row["filename"],
        extension=row["extension"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )