import os
import logging
from app.domain.models import DesignFile
from app.domain.repository import DesignRepository
from app.infrastructure.rabbitmq import publish_message

logger = logging.getLogger(__name__)
QUEUE_DESIGN_UPLOADED = "design.uploaded"
UPLOAD_DIR = "uploads"


class UploadDesignFileUseCase:
    def __init__(self, repo: DesignRepository):
        self.repo = repo

    async def execute(self, order_id: str, filename: str, file_content: bytes) -> DesignFile:
        logger.info(f"UploadDesignFileUseCase: processing file '{filename}' for order_id={order_id}")

        name, ext = os.path.splitext(filename)
        extension = ext.lstrip(".").lower() if ext else "unknown"

        logger.info(f"UploadDesignFileUseCase: file metadata - name='{name}', extension='{extension}'")

        os.makedirs(UPLOAD_DIR, exist_ok=True)
        save_path = os.path.join(UPLOAD_DIR, filename)
        with open(save_path, "wb") as f:
            f.write(file_content)
        logger.info(f"UploadDesignFileUseCase: file saved to '{save_path}'")

        design = DesignFile(
            order_id=order_id,
            filename=filename,
            extension=extension,
        )
        saved = await self.repo.save(design)

        await publish_message(QUEUE_DESIGN_UPLOADED, {
            "design_id": saved.id,
            "order_id": saved.order_id,
            "filename": saved.filename,
            "extension": saved.extension,
        })
        logger.info(f"UploadDesignFileUseCase: DesignEvent published for design_id={saved.id}")
        return saved


class ListDesignFilesUseCase:
    def __init__(self, repo: DesignRepository):
        self.repo = repo

    async def execute(self, order_id: str = None):
        if order_id:
            logger.info(f"ListDesignFilesUseCase: listing files for order_id={order_id}")
            return await self.repo.find_by_order_id(order_id)
        logger.info("ListDesignFilesUseCase: listing all design files")
        return await self.repo.find_all()
