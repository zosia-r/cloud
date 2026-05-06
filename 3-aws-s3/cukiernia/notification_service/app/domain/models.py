from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class Notification:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    order_id: str = ""
    recipient_email: str = ""
    message: str = ""
    notification_type: str = ""   # order_created | design_uploaded | inventory_reserved | payment_processed
    status: str = "sent"
    created_at: datetime = field(default_factory=datetime.utcnow)
