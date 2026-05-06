import aiosqlite
import logging
from typing import List, Optional
from datetime import datetime
from app.domain.models import Payment, PaymentStatus
from app.domain.repository import PaymentRepository

logger = logging.getLogger(__name__)
DB_PATH = "payment_service.db"


async def init_db():
    logger.info("Initializing PaymentService database")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
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
        await db.commit()
    logger.info("PaymentService database initialized")


class SQLitePaymentRepository(PaymentRepository):

    async def save(self, payment: Payment) -> Payment:
        logger.info(f"Saving payment id={payment.id} for order_id={payment.order_id}, amount={payment.amount}")
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO payments VALUES (?,?,?,?,?,?,?,?)",
                (payment.id, payment.order_id, payment.amount, payment.currency,
                 payment.status.value, payment.authorization_code,
                 payment.created_at.isoformat(), payment.updated_at.isoformat())
            )
            await db.commit()
        return payment

    async def find_by_id(self, payment_id: str) -> Optional[Payment]:
        logger.info(f"Looking up payment id={payment_id}")
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM payments WHERE id=?", (payment_id,))
            row = await cursor.fetchone()
        return _row_to_payment(row) if row else None

    async def find_by_order_id(self, order_id: str) -> Optional[Payment]:
        logger.info(f"Looking up payment for order_id={order_id}")
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM payments WHERE order_id=?", (order_id,))
            row = await cursor.fetchone()
        return _row_to_payment(row) if row else None

    async def find_all(self) -> List[Payment]:
        logger.info("Fetching all payments")
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM payments ORDER BY created_at DESC")
            rows = await cursor.fetchall()
        return [_row_to_payment(r) for r in rows]

    async def update_status(self, payment_id: str, status: str, auth_code: str = "") -> Optional[Payment]:
        logger.info(f"Updating payment id={payment_id} to status={status}, auth_code={auth_code}")
        now = datetime.utcnow().isoformat()
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE payments SET status=?, authorization_code=?, updated_at=? WHERE id=?",
                (status, auth_code, now, payment_id)
            )
            await db.commit()
        return await self.find_by_id(payment_id)


def _row_to_payment(row) -> Payment:
    return Payment(
        id=row["id"], order_id=row["order_id"],
        amount=row["amount"], currency=row["currency"],
        status=PaymentStatus(row["status"]),
        authorization_code=row["authorization_code"] or "",
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )
