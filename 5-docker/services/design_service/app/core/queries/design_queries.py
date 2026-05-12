from dataclasses import dataclass
from diator.requests import Request



# ── QUERIES ───────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class GetDesignQuery(Request):
    design_id: str


@dataclass(frozen=True)
class GetDownloadUrlQuery(Request):
    """Pobiera tymczasowy presigned URL z S3 do pobrania pliku."""
    design_id: str
    expiration_seconds: int = 3600


@dataclass(frozen=True)
class ListDesignsQuery(Request):
    order_id: str | None = None
