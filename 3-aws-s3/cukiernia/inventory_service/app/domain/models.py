from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class Ingredient:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    quantity: float = 0.0
    unit: str = "szt"
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Reservation:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    order_id: str = ""
    ingredient_name: str = ""
    quantity_reserved: float = 0.0
    status: str = "reserved"
    created_at: datetime = field(default_factory=datetime.utcnow)
