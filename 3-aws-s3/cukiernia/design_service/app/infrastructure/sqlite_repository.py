import aiosqlite
import logging
from typing import List, Optional
from datetime import datetime
from app.domain.models import DesignFile
from app.domain.repository import DesignRepository

logger = logging.getLogger(__name__)
DB_PATH = "design_service.db"


async def init_db():
    logger.info("Inicjalizacja bazy DesignService")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS design_files (
                id TEXT PRIMARY KEY,
                order_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                extension TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                s3_key TEXT NOT NULL,
                s3_url TEXT NOT NULL,
                uploaded_at TEXT NOT NULL
            )
        """)
        await db.commit()
    logger.info("Baza DesignService zainicjalizowana")


class SQLiteDesignRepository(DesignRepository):

    async def save(self, design: DesignFile) -> DesignFile:
        logger.info(f"save: design id={design.id}, filename={design.filename}, s3_key={design.s3_key}")
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO design_files VALUES (?,?,?,?,?,?,?,?)",
                (design.id, design.order_id, design.filename, design.extension,
                 design.file_size, design.s3_key, design.s3_url,
                 design.uploaded_at.isoformat())
            )
            await db.commit()
        return design

    async def find_by_id(self, design_id: str) -> Optional[DesignFile]:
        logger.info(f"find_by_id: design_id={design_id}")
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM design_files WHERE id=?", (design_id,))
            row = await cursor.fetchone()
        return _row_to_design(row) if row else None

    async def find_by_order_id(self, order_id: str) -> List[DesignFile]:
        logger.info(f"find_by_order_id: order_id={order_id}")
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM design_files WHERE order_id=?", (order_id,)
            )
            rows = await cursor.fetchall()
        return [_row_to_design(r) for r in rows]

    async def find_all(self) -> List[DesignFile]:
        logger.info("find_all: pobieranie wszystkich plików")
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM design_files ORDER BY uploaded_at DESC")
            rows = await cursor.fetchall()
        return [_row_to_design(r) for r in rows]


def _row_to_design(row) -> DesignFile:
    return DesignFile(
        id=row["id"], order_id=row["order_id"],
        filename=row["filename"], extension=row["extension"],
        file_size=row["file_size"], s3_key=row["s3_key"],
        s3_url=row["s3_url"],
        uploaded_at=datetime.fromisoformat(row["uploaded_at"]),
    )
