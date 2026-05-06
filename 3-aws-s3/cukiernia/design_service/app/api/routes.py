from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import logging
from mediator import Mediator
from app.core.commands.design_commands import (
    UploadDesignCommand, GetDesignQuery, GetDownloadUrlQuery, ListDesignsQuery
)
from app.core.handlers import (
    UploadDesignHandler, GetDesignHandler,
    GetDownloadUrlHandler, ListDesignsHandler
)
from app.infrastructure.sqlite_repository import SQLiteDesignRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/designs", tags=["designs"])


def get_mediator() -> Mediator:
    repo = SQLiteDesignRepository()
    m = Mediator()
    m.register_command(UploadDesignCommand, UploadDesignHandler(repo))
    m.register_query(GetDesignQuery, GetDesignHandler(repo))
    m.register_query(GetDownloadUrlQuery, GetDownloadUrlHandler(repo))
    m.register_query(ListDesignsQuery, ListDesignsHandler(repo))
    return m


@router.post("/upload", status_code=201)
async def upload_design(
    order_id: str = Form(...),
    file = File(...),
):
    logger.info(f"POST /designs/upload - order_id={order_id}, filename={file.filename}")
    content = await file.read()
    m = get_mediator()
    design_id = await m.send(UploadDesignCommand(
        order_id=order_id,
        filename=file.filename,
        file_content=content,
        content_type=file.content_type or "application/octet-stream",
    ))
    # Pobierz metadane żeby zwrócić kompletną odpowiedź
    design = await m.query(GetDesignQuery(design_id=design_id))
    return {
        "design_id": design.id,
        "order_id": design.order_id,
        "filename": design.filename,
        "extension": design.extension,
        "file_size": design.file_size,
        "s3_key": design.s3_key,
        "uploaded_at": design.uploaded_at.isoformat(),
        "message": "Plik zapisany w S3, metadane w bazie danych",
    }


@router.get("/{design_id}/download")
async def download_design(design_id: str, expiration: int = 3600):
    """
    Zwraca tymczasowy presigned URL do pobrania pliku z S3.
    Parametr expiration — czas ważności URL w sekundach (domyślnie 1h).
    """
    logger.info(f"GET /designs/{design_id}/download - expiration={expiration}s")
    try:
        m = get_mediator()
        result = await m.query(GetDownloadUrlQuery(
            design_id=design_id,
            expiration_seconds=expiration,
        ))
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{design_id}")
async def get_design(design_id: str):
    logger.info(f"GET /designs/{design_id}")
    try:
        m = get_mediator()
        design = await m.query(GetDesignQuery(design_id=design_id))
        return {
            "id": design.id, "order_id": design.order_id,
            "filename": design.filename, "extension": design.extension,
            "file_size": design.file_size, "s3_key": design.s3_key,
            "uploaded_at": design.uploaded_at.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/")
async def list_designs(order_id: Optional[str] = None):
    logger.info(f"GET /designs - order_id={order_id}")
    m = get_mediator()
    designs = await m.query(ListDesignsQuery(order_id=order_id or ""))
    return [
        {"id": d.id, "order_id": d.order_id, "filename": d.filename,
         "extension": d.extension, "file_size": d.file_size,
         "s3_key": d.s3_key, "uploaded_at": d.uploaded_at.isoformat()}
        for d in designs
    ]
