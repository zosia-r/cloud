import logging
from typing import Optional
from fastapi import APIRouter
from mediator import Mediator
from app.domain.models import SendNotificationCommand, ListNotificationsQuery
from app.core.handlers import SendNotificationHandler, ListNotificationsHandler
from app.infrastructure.sqlite_repository import SQLiteNotificationRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notifications", tags=["notifications"])


def get_mediator():
    repo = SQLiteNotificationRepository()
    m = Mediator()
    m.register_command(SendNotificationCommand, SendNotificationHandler(repo))
    m.register_query(ListNotificationsQuery, ListNotificationsHandler(repo))
    return m


@router.get("/")
async def list_notifications(order_id: Optional[str] = None):
    m = get_mediator()
    items = await m.query(ListNotificationsQuery(order_id=order_id))
    return [{"id": n.id, "order_id": n.order_id, "recipient_email": n.recipient_email,
             "message": n.message, "notification_type": n.notification_type,
             "status": n.status, "created_at": n.created_at.isoformat()} for n in items]


@router.post("/send", status_code=201)
async def send_notification(body: dict):
    m = get_mediator()
    nid = await m.send(SendNotificationCommand(
        order_id=body.get("order_id", ""), recipient_email=body.get("recipient_email", ""),
        message=body.get("message", ""), notification_type=body.get("notification_type", "manual")))
    return {"notification_id": nid, "status": "sent"}
