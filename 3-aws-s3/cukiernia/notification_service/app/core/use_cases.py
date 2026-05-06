import logging
from typing import List, Optional
from app.domain.models import Notification
from app.domain.repository import NotificationRepository

logger = logging.getLogger(__name__)


class ListNotificationsUseCase:
    def __init__(self, repo: NotificationRepository):
        self.repo = repo

    async def execute(self, order_id: Optional[str] = None) -> List[Notification]:
        if order_id:
            logger.info(f"ListNotificationsUseCase: listing notifications for order_id={order_id}")
            return await self.repo.find_by_order_id(order_id)
        logger.info("ListNotificationsUseCase: listing all notifications")
        return await self.repo.find_all()


class SendManualNotificationUseCase:
    def __init__(self, repo: NotificationRepository):
        self.repo = repo

    async def execute(self, order_id: str, recipient_email: str,
                      message: str, notification_type: str = "manual") -> Notification:
        logger.info(f"SendManualNotificationUseCase: sending manual notification for order_id={order_id}")
        notification = Notification(
            order_id=order_id,
            recipient_email=recipient_email,
            message=message,
            notification_type=notification_type,
            status="sent",
        )
        saved = await self.repo.save(notification)
        logger.info(f"SendManualNotificationUseCase: notification id={saved.id} saved and sent")
        return saved
