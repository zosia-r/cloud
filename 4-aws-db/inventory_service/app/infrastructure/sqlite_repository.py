import aiosqlite
import logging
from typing import List, Optional
from datetime import datetime
from app.domain.models import Ingredient, Reservation

logger = logging.getLogger(__name__)
DB_PATH = "inventory_service.db"


async def init_db():
    logger.info("Inicjalizacja bazy InventoryService")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS ingredients (
                id TEXT PRIMARY KEY, name TEXT UNIQUE NOT NULL,
                quantity REAL NOT NULL, unit TEXT NOT NULL, updated_at TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS reservations (
                id TEXT PRIMARY KEY, order_id TEXT NOT NULL,
                ingredient_name TEXT NOT NULL, quantity_reserved REAL NOT NULL,
                status TEXT NOT NULL, created_at TEXT NOT NULL
            )
        """)
        await db.execute("""
            INSERT OR IGNORE INTO ingredients VALUES
            ('s1','mąka',100.0,'kg','2024-01-01T00:00:00'),
            ('s2','cukier',50.0,'kg','2024-01-01T00:00:00'),
            ('s3','masło',30.0,'kg','2024-01-01T00:00:00'),
            ('s4','jajka',200.0,'szt','2024-01-01T00:00:00'),
            ('s5','śmietana',20.0,'l','2024-01-01T00:00:00')
        """)
        await db.commit()
    logger.info("Baza InventoryService zainicjalizowana")


class SQLiteIngredientRepository:
    async def find_by_name(self, name: str) -> Optional[Ingredient]:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            c = await db.execute("SELECT * FROM ingredients WHERE name=?", (name,))
            row = await c.fetchone()
        if not row:
            return None
        return Ingredient(id=row["id"], name=row["name"], quantity=row["quantity"],
                          unit=row["unit"], updated_at=datetime.fromisoformat(row["updated_at"]))

    async def find_all(self) -> List[Ingredient]:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            c = await db.execute("SELECT * FROM ingredients ORDER BY name")
            rows = await c.fetchall()
        return [Ingredient(id=r["id"], name=r["name"], quantity=r["quantity"],
                           unit=r["unit"], updated_at=datetime.fromisoformat(r["updated_at"]))
                for r in rows]

    async def update_quantity(self, name: str, quantity: float):
        now = datetime.utcnow().isoformat()
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE ingredients SET quantity=?, updated_at=? WHERE name=?",
                             (quantity, now, name))
            await db.commit()


class SQLiteReservationRepository:
    async def save(self, r: Reservation) -> Reservation:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT INTO reservations VALUES (?,?,?,?,?,?)",
                             (r.id, r.order_id, r.ingredient_name, r.quantity_reserved,
                              r.status, r.created_at.isoformat()))
            await db.commit()
        return r

    async def find_by_order_id(self, order_id: str) -> List[Reservation]:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            c = await db.execute("SELECT * FROM reservations WHERE order_id=?", (order_id,))
            rows = await c.fetchall()
        return [_row_to_res(r) for r in rows]

    async def find_all(self) -> List[Reservation]:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            c = await db.execute("SELECT * FROM reservations ORDER BY created_at DESC")
            rows = await c.fetchall()
        return [_row_to_res(r) for r in rows]


def _row_to_res(row) -> Reservation:
    return Reservation(id=row["id"], order_id=row["order_id"],
                       ingredient_name=row["ingredient_name"],
                       quantity_reserved=row["quantity_reserved"],
                       status=row["status"],
                       created_at=datetime.fromisoformat(row["created_at"]))
