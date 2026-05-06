import uuid
from dataclasses import dataclass, field
from datetime import datetime
from mediator import Command, Query


@dataclass
class Notification:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    order_id: str = ""
    recipient_email: str = ""
    message: str = ""
    notification_type: str = ""
    status: str = "sent"
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SendNotificationCommand(Command):
    order_id: str
    recipient_email: str
    message: str
    notification_type: str


@dataclass
class ListNotificationsQuery(Query):
    order_id: str = None
