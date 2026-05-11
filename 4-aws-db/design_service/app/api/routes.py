from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import logging
from diator.mediator import Mediator
from diator.requests import RequestMap
from app.core.commands.design_commands import (
    UploadDesignCommand
)
from app.core.queries.design_queries import GetDesignQuery, GetDownloadUrlQuery, ListDesignsQuery
from app.core.handlers import (
    UploadDesignHandler, GetDesignHandler,
    GetDownloadUrlHandler, ListDesignsHandler
)
from app.infrastructure.dynamodb_repository import DynamoDBDesignRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/designs", tags=["designs"])

# Singleton mediator instance
_mediator: Optional[Mediator] = None

# Simple container for handler instances
class SimpleContainer:
    def __init__(self, handlers_map: dict):
        self.handlers = handlers_map
    
    async def resolve(self, handler_type):
        return self.handlers.get(handler_type)

def get_mediator() -> Mediator:
    global _mediator
    if _mediator is not None:
        return _mediator
    
    repo = DynamoDBDesignRepository()
    
    # Create handler instances
    upload_handler = UploadDesignHandler(repo)
    get_design_handler = GetDesignHandler(repo)
    get_download_url_handler = GetDownloadUrlHandler(repo)
    list_designs_handler = ListDesignsHandler(repo)
    
    # Setup simple container with handler instances
    container = SimpleContainer({
        UploadDesignHandler: upload_handler,
        GetDesignHandler: get_design_handler,
        GetDownloadUrlHandler: get_download_url_handler,
        ListDesignsHandler: list_designs_handler,
    })
    
    # Setup request map
    request_map = RequestMap()
    request_map.bind(UploadDesignCommand, UploadDesignHandler)
    request_map.bind(GetDesignQuery, GetDesignHandler)
    request_map.bind(GetDownloadUrlQuery, GetDownloadUrlHandler)
    request_map.bind(ListDesignsQuery, ListDesignsHandler)
    
    # Create mediator
    _mediator = Mediator(
        request_map=request_map,
        container=container,
    )
    return _mediator


@router.post("/upload", status_code=201)
async def upload_design(
    order_id: str = Form(...),
    file = File(...),
):
    logger.info(f"POST /designs/upload - order_id={order_id}, filename={file.filename}")
    content = await file.read()
    mediator = get_mediator()
    design_id = await mediator.send(UploadDesignCommand(
        order_id=order_id,
        filename=file.filename,
        file_content=content,
        content_type=file.content_type or "application/octet-stream",
    ))
    # Pobierz metadane żeby zwrócić kompletną odpowiedź
    design = await mediator.send(GetDesignQuery(design_id=design_id))
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
        mediator = get_mediator()
        result = await mediator.send(GetDownloadUrlQuery(
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
        mediator = get_mediator()
        design = await mediator.send(GetDesignQuery(design_id=design_id))
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
    mediator = get_mediator()
    designs = await mediator.send(ListDesignsQuery(order_id=order_id or ""))
    return [
        {"id": d.id, "order_id": d.order_id, "filename": d.filename,
         "extension": d.extension, "file_size": d.file_size,
         "s3_key": d.s3_key, "uploaded_at": d.uploaded_at.isoformat()}
        for d in designs
    ]
