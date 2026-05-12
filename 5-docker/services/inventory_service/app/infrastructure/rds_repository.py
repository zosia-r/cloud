import asyncpg
import logging
import os
from typing import List, Optional
from datetime import datetime
from app.domain.models import Ingredient, Reservation

logger = logging.getLogger(__name__)


async def init_db():
    """Initialize RDS (PostgreSQL) connection"""
    global _pool
    try:
        db_host = os.getenv("INVENTORY_DB_HOST", "localhost")
        db_port = int(os.getenv("RDS_PORT", "5432"))
        db_name = os.getenv("INVENTORY_DB_NAME", "inventory_db")
        db_user = os.getenv("RDS_USER", "postgres")
        db_password = os.getenv("RDS_PASSWORD", "")
        
        logger.info(f"Starting RDS connection for InventoryService to {db_host}:{db_port}/{db_name}")
        
        _pool = await asyncpg.create_pool(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password,
            min_size=1,
            max_size=10,
            timeout=30,
            ssl='require'
        )
        
        logger.info("RDS connection successful. Connection pool created")
        
        # Create tables if they don't exist
        async with _pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS ingredients (
                    id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    quantity REAL NOT NULL,
                    unit TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS reservations (
                    id TEXT PRIMARY KEY,
                    order_id TEXT NOT NULL,
                    ingredient_name TEXT NOT NULL,
                    quantity_reserved REAL NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            
            # Insert initial ingredients
            await conn.execute("""
                INSERT INTO ingredients (id, name, quantity, unit, updated_at)
                VALUES 
                    ('s1', 'mąka', 100.0, 'kg', '2024-01-01T00:00:00'),
                    ('s2', 'cukier', 50.0, 'kg', '2024-01-01T00:00:00'),
                    ('s3', 'masło', 30.0, 'kg', '2024-01-01T00:00:00'),
                    ('s4', 'jajka', 200.0, 'szt', '2024-01-01T00:00:00'),
                    ('s5', 'śmietana', 20.0, 'l', '2024-01-01T00:00:00')
                ON CONFLICT (id) DO NOTHING
            """)
            
        logger.info("InventoryService RDS tables initialized successfully")
        
    except Exception as e:
        logger.error(f"RDS connection failed: {str(e)}", exc_info=True)
        raise


class RDSIngredientRepository:
    async def find_by_name(self, name: str) -> Optional[Ingredient]:
        async with _pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM ingredients WHERE name=$1", name)
        if not row:
            return None
        return Ingredient(
            id=row['id'],
            name=row['name'],
            quantity=row['quantity'],
            unit=row['unit'],
            updated_at=datetime.fromisoformat(row['updated_at'])
        )

    async def find_all(self) -> List[Ingredient]:
        async with _pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM ingredients ORDER BY name")
        return [
            Ingredient(
                id=r['id'],
                name=r['name'],
                quantity=r['quantity'],
                unit=r['unit'],
                updated_at=datetime.fromisoformat(r['updated_at'])
            ) for r in rows
        ]

    async def update_quantity(self, name: str, quantity: float):
        now = datetime.utcnow().isoformat()
        async with _pool.acquire() as conn:
            await conn.execute(
                "UPDATE ingredients SET quantity=$1, updated_at=$2 WHERE name=$3",
                quantity, now, name
            )


class RDSReservationRepository:
    async def save(self, r: Reservation) -> Reservation:
        logger.info(f"save: reservation id={r.id}, order_id={r.order_id}")
        async with _pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO reservations (id, order_id, ingredient_name, quantity_reserved, status, created_at) VALUES ($1, $2, $3, $4, $5, $6)",
                r.id, r.order_id, r.ingredient_name, r.quantity_reserved, r.status, r.created_at.isoformat()
            )
        logger.info(f"Reservation saved successfully: id={r.id}")
        return r

    async def find_by_order_id(self, order_id: str) -> List[Reservation]:
        logger.info(f"find_by_order_id: order_id={order_id}")
        async with _pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM reservations WHERE order_id=$1", order_id)
        reservations = [
            Reservation(
                id=r['id'],
                order_id=r['order_id'],
                ingredient_name=r['ingredient_name'],
                quantity_reserved=r['quantity_reserved'],
                status=r['status'],
                created_at=datetime.fromisoformat(r['created_at'])
            ) for r in rows
        ]
        logger.info(f"Found {len(reservations)} reservations for order_id={order_id}")
        return reservations

    async def find_all(self) -> List[Reservation]:
        logger.info("find_all: fetching all reservations")
        async with _pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM reservations ORDER BY created_at DESC")
        reservations = [
            Reservation(
                id=r['id'],
                order_id=r['order_id'],
                ingredient_name=r['ingredient_name'],
                quantity_reserved=r['quantity_reserved'],
                status=r['status'],
                created_at=datetime.fromisoformat(r['created_at'])
            ) for r in rows
        ]
        logger.info(f"Found {len(reservations)} total reservations")
        return reservations
