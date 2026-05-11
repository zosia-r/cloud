from dataclasses import dataclass
from diator.requests import Request


# ── COMMANDS ──────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class UploadDesignCommand(Request):
    order_id: str
    filename: str
    file_content: bytes
    content_type: str = "application/octet-stream"


