from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class PaymentStatus(str, Enum):
    PENDING = "pending"
    AUTHORIZED = "authorized"
    FAILED = "failed"
    REFUNDED = "refunded"


@dataclass
class Payment:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    order_id: str = ""
    amount: float = 0.0
    currency: str = "PLN"
    status: PaymentStatus = PaymentStatus.PENDING
    authorization_code: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
