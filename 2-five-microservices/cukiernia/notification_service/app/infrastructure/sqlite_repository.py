import aiosqlite
import logging
from typing import List
from datetime import datetime
from app.domain.models import Notification
from app.domain.repository import NotificationRepository

logger = logging.getLogger(__name__)
DB_PATH = "notification_service.db"


async def init_db():
    logger.info("Initializing NotificationService database")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id TEXT PRIMARY KEY,
                order_id TEXT NOT NULL,
                recipient_email TEXT NOT NULL,
                message TEXT NOT NULL,
                notification_type TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        await db.commit()
    logger.info("NotificationService database initialized")


class SQLiteNotificationRepository(NotificationRepository):

    async def save(self, notification: Notification) -> Notification:
        logger.info(f"Saving notification id={notification.id}, type={notification.notification_type}, order_id={notification.order_id}")
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT INTO notifications VALUES (?,?,?,?,?,?,?)",
                (notification.id, notification.order_id, notification.recipient_email,
                 notification.message, notification.notification_type,
                 notification.status, notification.created_at.isoformat())
            )
            await db.commit()
        logger.info(f"Notification id={notification.id} saved")
        return notification

    async def find_by_order_id(self, order_id: str) -> List[Notification]:
        logger.info(f"Fetching notifications for order_id={order_id}")
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM notifications WHERE order_id=? ORDER BY created_at DESC",
                (order_id,)
            )
            rows = await cursor.fetchall()
        return [_row_to_notification(r) for r in rows]

    async def find_all(self) -> List[Notification]:
        logger.info("Fetching all notifications")
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM notifications ORDER BY created_at DESC")
            rows = await cursor.fetchall()
        return [_row_to_notification(r) for r in rows]


def _row_to_notification(row) -> Notification:
    return Notification(
        id=row["id"],
        order_id=row["order_id"],
        recipient_email=row["recipient_email"],
        message=row["message"],
        notification_type=row["notification_type"],
        status=row["status"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )
