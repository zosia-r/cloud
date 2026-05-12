import uuid
from dataclasses import dataclass, field
from datetime import datetime
from diator.requests import Request


@dataclass
class Notification:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    order_id: str = ""
    recipient_email: str = ""
    message: str = ""
    notification_type: str = ""
    status: str = "sent"
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class SendNotificationCommand(Request):
    order_id: str
    recipient_email: str
    message: str
    notification_type: str


@dataclass(frozen=True)
class ListNotificationsQuery(Request):
    order_id: str = None
