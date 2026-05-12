import aiosqlite, logging
from typing import List, Optional
from datetime import datetime
from app.domain.models import Payment, PaymentStatus

logger = logging.getLogger(__name__)
DB_PATH = "payment_service.db"


async def init_db():
    logger.info("Inicjalizacja bazy PaymentService")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id TEXT PRIMARY KEY, order_id TEXT NOT NULL,
                amount REAL NOT NULL, currency TEXT NOT NULL,
                status TEXT NOT NULL, authorization_code TEXT,
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            )
        """)
        await db.commit()
    logger.info("Baza PaymentService zainicjalizowana")


class SQLitePaymentRepository:
    async def save(self, p: Payment) -> Payment:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT INTO payments VALUES (?,?,?,?,?,?,?,?)",
                (p.id, p.order_id, p.amount, p.currency, p.status.value,
                 p.authorization_code, p.created_at.isoformat(), p.updated_at.isoformat()))
            await db.commit()
        return p

    async def find_by_order_id(self, order_id: str) -> Optional[Payment]:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            c = await db.execute("SELECT * FROM payments WHERE order_id=?", (order_id,))
            row = await c.fetchone()
        return _row(row) if row else None

    async def find_all(self) -> List[Payment]:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            c = await db.execute("SELECT * FROM payments ORDER BY created_at DESC")
            rows = await c.fetchall()
        return [_row(r) for r in rows]

    async def update_status(self, payment_id: str, status: str, auth_code: str) -> None:
        now = datetime.utcnow().isoformat()
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE payments SET status=?, authorization_code=?, updated_at=? WHERE id=?",
                             (status, auth_code, now, payment_id))
            await db.commit()


def _row(row) -> Payment:
    return Payment(id=row["id"], order_id=row["order_id"], amount=row["amount"],
                   currency=row["currency"], status=PaymentStatus(row["status"]),
                   authorization_code=row["authorization_code"] or "",
                   created_at=datetime.fromisoformat(row["created_at"]),
                   updated_at=datetime.fromisoformat(row["updated_at"]))
