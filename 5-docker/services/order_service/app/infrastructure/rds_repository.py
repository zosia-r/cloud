import asyncpg
import logging
import os
from typing import List, Optional
from datetime import datetime
from app.domain.models import Order, OrderStatus
from app.domain.repository import OrderRepository

logger = logging.getLogger(__name__)


async def init_db():
    """Initialize RDS (PostgreSQL) connection"""
    global _pool
    try:
        db_host = os.getenv("ORDER_DB_HOST", "localhost")
        db_port = int(os.getenv("RDS_PORT", "5432"))
        db_name = os.getenv("ORDER_DB_NAME", "order_db")
        db_user = os.getenv("RDS_USER", "postgres")
        db_password = os.getenv("RDS_PASSWORD", "")
        
        logger.info(f"Starting RDS connection for OrderService to {db_host}:{db_port}/{db_name}")
        
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
        
        # Create table if it doesn't exist
        async with _pool.acquire() as conn:
            await conn.execute("""
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
            
        logger.info("OrderService RDS table initialized successfully")
        
    except Exception as e:
        logger.error(f"RDS connection failed: {str(e)}", exc_info=True)
        raise


class RDSOrderRepository(OrderRepository):

    async def save(self, order: Order) -> Order:
        logger.info(f"save: order id={order.id}")
        async with _pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO orders (id, customer_name, customer_email, product_description, quantity, status, created_at, updated_at) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)",
                order.id, order.customer_name, order.customer_email,
                order.product_description, order.quantity, order.status.value,
                order.created_at.isoformat(), order.updated_at.isoformat()
            )
        logger.info(f"Order saved successfully: id={order.id}")
        return order

    async def find_by_id(self, order_id: str) -> Optional[Order]:
        logger.info(f"find_by_id: order_id={order_id}")
        async with _pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM orders WHERE id=$1", order_id)
        if row:
            logger.info(f"Order found: id={order_id}")
            return self._row_to_order(row)
        logger.info(f"Order not found: id={order_id}")
        return None

    async def find_all(self) -> List[Order]:
        logger.info("find_all: fetching all orders")
        async with _pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM orders ORDER BY created_at DESC")
        orders = [self._row_to_order(r) for r in rows]
        logger.info(f"Found {len(orders)} total orders")
        return orders

    async def update_status(self, order_id: str, status: str) -> Optional[Order]:
        logger.info(f"update_status: order_id={order_id}, status={status}")
        now = datetime.utcnow().isoformat()
        async with _pool.acquire() as conn:
            await conn.execute(
                "UPDATE orders SET status=$1, updated_at=$2 WHERE id=$3",
                status, now, order_id
            )
        logger.info(f"Order status updated: id={order_id}, new_status={status}")
        return await self.find_by_id(order_id)

    def _row_to_order(self, row) -> Order:
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
