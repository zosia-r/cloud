import aiosqlite
import logging
from typing import List
from app.domain.models import Notification
from app.domain.repository import NotificationRepository

logger = logging.getLogger(__name__)
DB_PATH = "notification_service.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id TEXT PRIMARY KEY, order_id TEXT NOT NULL,
                recipient_email TEXT NOT NULL, message TEXT NOT NULL,
                notification_type TEXT NOT NULL, status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        await db.commit()


class SQLiteNotificationRepository(NotificationRepository):
    async def save(self, n: Notification) -> Notification:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT INTO notifications VALUES (?,?,?,?,?,?,?)",
                (n.id, n.order_id, n.recipient_email, n.message,
                 n.notification_type, n.status, n.created_at.isoformat()))
            await db.commit()
        return n

    async def find_by_order_id(self, order_id: str) -> List[Notification]:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            c = await db.execute("SELECT * FROM notifications WHERE order_id=? ORDER BY created_at DESC", (order_id,))
            rows = await c.fetchall()
        return [_row(r) for r in rows]

    async def find_all(self) -> List[Notification]:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            c = await db.execute("SELECT * FROM notifications ORDER BY created_at DESC")
            rows = await c.fetchall()
        return [_row(r) for r in rows]


def _row(row) -> Notification:
    return Notification(id=row["id"], order_id=row["order_id"],
                        recipient_email=row["recipient_email"], message=row["message"],
                        notification_type=row["notification_type"], status=row["status"],
                        created_at=__import__('datetime').datetime.fromisoformat(row["created_at"]))
