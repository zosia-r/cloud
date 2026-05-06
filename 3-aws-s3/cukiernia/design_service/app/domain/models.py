from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class DesignFile:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    order_id: str = ""
    filename: str = ""
    extension: str = ""
    file_size: int = 0           # rozmiar w bajtach
    s3_key: str = ""             # ścieżka w S3 np. "uploads/order-123/wzor.png"
    s3_url: str = ""             # presigned URL do pobrania
    uploaded_at: datetime = field(default_factory=datetime.utcnow)
