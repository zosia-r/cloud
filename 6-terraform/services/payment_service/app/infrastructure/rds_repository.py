import asyncpg
import logging
import os
from typing import List, Optional
from datetime import datetime
from app.domain.models import Payment, PaymentStatus

logger = logging.getLogger(__name__)

# Global connection pool
_pool = None


async def init_db():
    """Initialize RDS (PostgreSQL) connection"""
    global _pool
    try:
        db_host = os.getenv("PAYMENT_DB_HOST", "localhost")
        db_port = int(os.getenv("RDS_PORT", "5432"))
        db_name = os.getenv("PAYMENT_DB_NAME", "payment_db")
        db_user = os.getenv("RDS_USER", "postgres")
        db_password = os.getenv("RDS_PASSWORD", "")
        
        logger.info(f"Starting RDS connection for PaymentService to {db_host}:{db_port}/{db_name}")
        
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
                CREATE TABLE IF NOT EXISTS payments (
                    id TEXT PRIMARY KEY,
                    order_id TEXT NOT NULL,
                    amount REAL NOT NULL,
                    currency TEXT NOT NULL,
                    status TEXT NOT NULL,
                    authorization_code TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
        logger.info("PaymentService RDS table initialized successfully")
        
    except Exception as e:
        logger.error(f"RDS connection failed: {str(e)}", exc_info=True)
        raise


class RDSPaymentRepository:
    async def save(self, p: Payment) -> Payment:
        logger.info(f"save: payment id={p.id}, order_id={p.order_id}")
        async with _pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO payments (id, order_id, amount, currency, status, authorization_code, created_at, updated_at) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)",
                p.id, p.order_id, p.amount, p.currency, p.status.value,
                p.authorization_code, p.created_at.isoformat(), p.updated_at.isoformat()
            )
        logger.info(f"Payment saved successfully: id={p.id}")
        return p

    async def find_by_order_id(self, order_id: str) -> Optional[Payment]:
        logger.info(f"find_by_order_id: order_id={order_id}")
        async with _pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM payments WHERE order_id=$1", order_id)
        if row:
            logger.info(f"Payment found: order_id={order_id}")
            return self._row_to_payment(row)
        logger.info(f"Payment not found: order_id={order_id}")
        return None

    async def find_all(self) -> List[Payment]:
        logger.info("find_all: fetching all payments")
        async with _pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM payments ORDER BY created_at DESC")
        payments = [self._row_to_payment(r) for r in rows]
        logger.info(f"Found {len(payments)} total payments")
        return payments

    async def update_status(self, payment_id: str, status: str, auth_code: str) -> None:
        logger.info(f"update_status: payment_id={payment_id}, status={status}")
        now = datetime.utcnow().isoformat()
        async with _pool.acquire() as conn:
            await conn.execute(
                "UPDATE payments SET status=$1, authorization_code=$2, updated_at=$3 WHERE id=$4",
                status, auth_code, now, payment_id
            )
        logger.info(f"Payment status updated: id={payment_id}, new_status={status}")

    def _row_to_payment(self, row) -> Payment:
        return Payment(
            id=row["id"],
            order_id=row["order_id"],
            amount=row["amount"],
            currency=row["currency"],
            status=PaymentStatus(row["status"]),
            authorization_code=row["authorization_code"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"])
        )
