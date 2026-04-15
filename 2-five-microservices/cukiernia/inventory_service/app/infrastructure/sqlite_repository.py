import aiosqlite
import logging
from typing import List, Optional
from datetime import datetime
from app.domain.models import Ingredient, Reservation
from app.domain.repository import IngredientRepository, ReservationRepository

logger = logging.getLogger(__name__)
DB_PATH = "inventory_service.db"


async def init_db():
    logger.info("Initializing InventoryService database")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS ingredients (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                quantity REAL NOT NULL,
                unit TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS reservations (
                id TEXT PRIMARY KEY,
                order_id TEXT NOT NULL,
                ingredient_name TEXT NOT NULL,
                quantity_reserved REAL NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        # Seed some default ingredients
        await db.execute("""
            INSERT OR IGNORE INTO ingredients VALUES
            ('seed-1','mąka',100.0,'kg','2024-01-01T00:00:00'),
            ('seed-2','cukier',50.0,'kg','2024-01-01T00:00:00'),
            ('seed-3','masło',30.0,'kg','2024-01-01T00:00:00'),
            ('seed-4','jajka',200.0,'szt','2024-01-01T00:00:00'),
            ('seed-5','śmietana',20.0,'l','2024-01-01T00:00:00')
        """)
        await db.commit()
    logger.info("InventoryService database initialized with default ingredients")


class SQLiteIngredientRepository(IngredientRepository):

    async def save(self, ingredient: Ingredient) -> Ingredient:
        logger.info(f"Saving ingredient name={ingredient.name}, qty={ingredient.quantity}")
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT OR REPLACE INTO ingredients VALUES (?,?,?,?,?)",
                (ingredient.id, ingredient.name, ingredient.quantity,
                 ingredient.unit, ingredient.updated_at.isoformat())
            )
            await db.commit()
        return ingredient

    async def find_all(self) -> List[Ingredient]:
        logger.info("Fetching all ingredients")
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM ingredients ORDER BY name")
            rows = await cursor.fetchall()
        return [_row_to_ingredient(r) for r in rows]

    async def find_by_name(self, name: str) -> Optional[Ingredient]:
        logger.info(f"Looking up ingredient name={name}")
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM ingredients WHERE name=?", (name,))
            row = await cursor.fetchone()
        return _row_to_ingredient(row) if row else None

    async def update_quantity(self, name: str, quantity: float) -> Optional[Ingredient]:
        logger.info(f"Updating ingredient name={name} quantity to {quantity}")
        now = datetime.utcnow().isoformat()
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE ingredients SET quantity=?, updated_at=? WHERE name=?",
                (quantity, now, name)
            )
            await db.commit()
        return await self.find_by_name(name)


class SQLiteReservationRepository(ReservationRepository):

    async def save(self, reservation: Reservation) -> Reservation:
        logger.info(f"Saving reservation id={reservation.id} for order_id={reservation.order_id}")
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO reservations VALUES (?,?,?,?,?,?)",
                (reservation.id, reservation.order_id, reservation.ingredient_name,
                 reservation.quantity_reserved, reservation.status,
                 reservation.created_at.isoformat())
            )
            await db.commit()
        return reservation

    async def find_by_order_id(self, order_id: str) -> List[Reservation]:
        logger.info(f"Fetching reservations for order_id={order_id}")
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM reservations WHERE order_id=?", (order_id,)
            )
            rows = await cursor.fetchall()
        return [_row_to_reservation(r) for r in rows]

    async def find_all(self) -> List[Reservation]:
        logger.info("Fetching all reservations")
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM reservations ORDER BY created_at DESC")
            rows = await cursor.fetchall()
        return [_row_to_reservation(r) for r in rows]


def _row_to_ingredient(row) -> Ingredient:
    return Ingredient(
        id=row["id"], name=row["name"], quantity=row["quantity"],
        unit=row["unit"], updated_at=datetime.fromisoformat(row["updated_at"])
    )


def _row_to_reservation(row) -> Reservation:
    return Reservation(
        id=row["id"], order_id=row["order_id"],
        ingredient_name=row["ingredient_name"],
        quantity_reserved=row["quantity_reserved"],
        status=row["status"],
        created_at=datetime.fromisoformat(row["created_at"])
    )