from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
import logging
from app.core.use_cases import ListNotificationsUseCase, SendManualNotificationUseCase
from app.infrastructure.sqlite_repository import SQLiteNotificationRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notifications", tags=["notifications"])


def get_repo():
    return SQLiteNotificationRepository()


class ManualNotificationRequest(BaseModel):
    order_id: str
    recipient_email: str
    message: str
    notification_type: str = "manual"


@router.get("/")
async def list_notifications(order_id: Optional[str] = None, repo=Depends(get_repo)):
    logger.info(f"GET /notifications - order_id={order_id}")
    uc = ListNotificationsUseCase(repo)
    items = await uc.execute(order_id)
    return [
        {
            "id": n.id,
            "order_id": n.order_id,
            "recipient_email": n.recipient_email,
            "message": n.message,
            "notification_type": n.notification_type,
            "status": n.status,
            "created_at": n.created_at.isoformat(),
        }
        for n in items
    ]


@router.post("/send", status_code=201)
async def send_manual_notification(body: ManualNotificationRequest, repo=Depends(get_repo)):
    logger.info(f"POST /notifications/send - order_id={body.order_id}, recipient={body.recipient_email}")
    uc = SendManualNotificationUseCase(repo)
    notification = await uc.execute(
        body.order_id, body.recipient_email, body.message, body.notification_type
    )
    return {
        "notification_id": notification.id,
        "order_id": notification.order_id,
        "recipient_email": notification.recipient_email,
        "status": notification.status,
        "message": "Notification sent successfully",
    }
