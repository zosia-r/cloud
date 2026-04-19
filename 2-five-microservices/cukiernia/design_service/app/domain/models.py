from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class DesignFile:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    order_id: str = ""
    filename: str = ""
    extension: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
