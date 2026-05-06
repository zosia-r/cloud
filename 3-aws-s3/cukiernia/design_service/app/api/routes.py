from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import Optional
import logging
from app.core.use_cases import UploadDesignFileUseCase, ListDesignFilesUseCase
from app.infrastructure.sqlite_repository import SQLiteDesignRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/designs", tags=["designs"])


def get_repo():
    return SQLiteDesignRepository()


@router.post("/upload", status_code=201)
async def upload_design(
    order_id: str = Form(...),
    file: UploadFile = File(...),
    repo=Depends(get_repo)
):
    logger.info(f"POST /designs/upload - order_id={order_id}, filename={file.filename}")
    content = await file.read()
    uc = UploadDesignFileUseCase(repo)
    design = await uc.execute(order_id, file.filename, content)
    return {
        "design_id": design.id,
        "order_id": design.order_id,
        "filename": design.filename,
        "extension": design.extension,
        "message": "Design file uploaded and logged successfully"
    }


@router.get("/")
async def list_designs(order_id: Optional[str] = None, repo=Depends(get_repo)):
    logger.info(f"GET /designs - order_id filter={order_id}")
    uc = ListDesignFilesUseCase(repo)
    designs = await uc.execute(order_id)
    return [
        {"id": d.id, "order_id": d.order_id, "filename": d.filename,
         "extension": d.extension, "created_at": d.created_at.isoformat()}
        for d in designs
    ]
