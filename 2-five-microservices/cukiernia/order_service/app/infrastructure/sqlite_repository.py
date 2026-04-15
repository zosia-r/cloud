import aiosqlite
import logging
from typing import List, Optional
from datetime import datetime
from app.domain.models import Order, OrderStatus
from app.domain.repository import OrderRepository

logger = logging.getLogger(__name__)
DB_PATH = "order_service.db"


async def init_db():
    logger.info("Initializing OrderService database")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                customer_name TEXT NOT NULL,
                customer_email TEXT NOT NULL,
                product_description TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        await db.commit()
    logger.info("OrderService database initialized")


class SQLiteOrderRepository(OrderRepository):

    async def save(self, order: Order) -> Order:
        logger.info(f"Saving order id={order.id} to database")
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO orders VALUES (?,?,?,?,?,?,?,?)",
                (order.id, order.customer_name, order.customer_email,
                 order.product_description, order.quantity, order.status.value,
                 order.created_at.isoformat(), order.updated_at.isoformat())
            )
            await db.commit()
        logger.info(f"Order id={order.id} saved successfully")
        return order

    async def find_by_id(self, order_id: str) -> Optional[Order]:
        logger.info(f"Looking up order id={order_id}")
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM orders WHERE id=?", (order_id,))
            row = await cursor.fetchone()
        if not row:
            logger.warning(f"Order id={order_id} not found")
            return None
        return _row_to_order(row)

    async def find_all(self) -> List[Order]:
        logger.info("Fetching all orders from database")
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM orders ORDER BY created_at DESC")
            rows = await cursor.fetchall()
        logger.info(f"Found {len(rows)} orders")
        return [_row_to_order(r) for r in rows]

    async def update_status(self, order_id: str, status: str) -> Optional[Order]:
        logger.info(f"Updating order id={order_id} status to {status}")
        now = datetime.utcnow().isoformat()
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE orders SET status=?, updated_at=? WHERE id=?",
                (status, now, order_id)
            )
            await db.commit()
        return await self.find_by_id(order_id)


def _row_to_order(row) -> Order:
    return Order(
        id=row["id"],
        customer_name=row["customer_name"],
        customer_email=row["customer_email"],
        product_description=row["product_description"],
        quantity=row["quantity"],
        status=OrderStatus(row["status"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )