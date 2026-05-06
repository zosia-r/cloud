from mediator import Command, Query
from dataclasses import dataclass


# ── COMMANDS ──────────────────────────────────────────────────────────────────

@dataclass
class UploadDesignCommand(Command):
    order_id: str
    filename: str
    file_content: bytes
    content_type: str = "application/octet-stream"


# ── QUERIES ───────────────────────────────────────────────────────────────────

@dataclass
class GetDesignQuery(Query):
    design_id: str


@dataclass
class GetDownloadUrlQuery(Query):
    """Pobiera tymczasowy presigned URL z S3 do pobrania pliku."""
    design_id: str
    expiration_seconds: int = 3600


@dataclass
class ListDesignsQuery(Query):
    order_id: str | None = None
