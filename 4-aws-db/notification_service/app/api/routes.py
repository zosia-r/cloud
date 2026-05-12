import logging
from typing import Optional
from fastapi import APIRouter
from diator.mediator import Mediator
from diator.requests import RequestMap
from app.domain.models import SendNotificationCommand, ListNotificationsQuery
from app.core.handlers import SendNotificationHandler, ListNotificationsHandler
from app.infrastructure.dynamodb_repository import get_notification_repository
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/notifications", tags=["notifications"])

# Singleton mediator instance
_mediator: Optional[Mediator] = None

# Simple container for handler instances
class SimpleContainer:
    def __init__(self, handlers_map: dict):
        self.handlers = handlers_map
    
    async def resolve(self, handler_type):
        return self.handlers.get(handler_type)

def get_mediator() -> Mediator:
    global _mediator
    if _mediator is not None:
        return _mediator
    
    repo = get_notification_repository()
    
    # Create handler instances
    send_handler = SendNotificationHandler(repo)
    list_handler = ListNotificationsHandler(repo)
    
    # Setup simple container with handler instances
    container = SimpleContainer({
        SendNotificationHandler: send_handler,
        ListNotificationsHandler: list_handler,
    })
    
    # Setup request map
    request_map = RequestMap()
    request_map.bind(SendNotificationCommand, SendNotificationHandler)
    request_map.bind(ListNotificationsQuery, ListNotificationsHandler)
    
    # Create mediator
    _mediator = Mediator(
        request_map=request_map,
        container=container,
    )
    return _mediator


@router.get("/")
async def list_notifications(order_id: Optional[str] = None):
    mediator = get_mediator()
    items = await mediator.send(ListNotificationsQuery(order_id=order_id))
    return [{"id": n.id, "order_id": n.order_id, "recipient_email": n.recipient_email,
             "message": n.message, "notification_type": n.notification_type,
             "status": n.status, "created_at": n.created_at.isoformat()} for n in items]


@router.post("/send", status_code=201)
async def send_notification(body: dict):
    mediator = get_mediator()
    nid = await mediator.send(SendNotificationCommand(
        order_id=body.get("order_id", ""), recipient_email=body.get("recipient_email", ""),
        message=body.get("message", ""), notification_type=body.get("notification_type", "manual")))
    return {"notification_id": nid, "status": "sent"}
