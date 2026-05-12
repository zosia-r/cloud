import os
import logging
from diator.requests import RequestHandler
from app.domain.models import DesignFile
from app.domain.repository import DesignRepository
from app.core.commands.design_commands import (
    UploadDesignCommand
)
from app.core.queries.design_queries import GetDesignQuery, GetDownloadUrlQuery, ListDesignsQuery
from app.infrastructure.s3_client import upload_file_to_s3, generate_presigned_url
from app.infrastructure.rabbitmq import publish_message

logger = logging.getLogger(__name__)
QUEUE_DESIGN_UPLOADED = "design.uploaded"


# ── COMMAND HANDLERS ──────────────────────────────────────────────────────────

class UploadDesignHandler(RequestHandler[UploadDesignCommand, str]):
    """
    CQS: Command — uploaduje plik do S3, zapisuje metadane w bazie, publikuje event.
    """
    def __init__(self, repo: DesignRepository):
        self.repo = repo

    async def handle(self, command: UploadDesignCommand) -> str:
        filename = command.filename
        name, ext = os.path.splitext(filename)
        extension = ext.lstrip(".").lower() if ext else "unknown"
        file_size = len(command.file_content)

        logger.info(
            f"UploadDesignHandler: plik='{filename}', "
            f"rozszerzenie='{extension}', rozmiar={file_size} bajtów, "
            f"order_id={command.order_id}"
        )

        # Klucz w S3: uploads/{order_id}/{filename}
        s3_key = f"uploads/{command.order_id}/{filename}"

        # Upload do S3
        try:
            await upload_file_to_s3(command.file_content, s3_key, command.content_type)
        except Exception as e:
            logger.error(f"UploadDesignHandler: błąd uploadu do S3: {e}")
            raise

        # Generuj presigned URL (ważny 1h)
        s3_url = await generate_presigned_url(s3_key, expiration_seconds=3600)

        # Zapisz metadane w bazie
        design = DesignFile(
            order_id=command.order_id,
            filename=filename,
            extension=extension,
            file_size=file_size,
            s3_key=s3_key,
            s3_url=s3_url,
        )
        saved = await self.repo.save(design)
        logger.info(f"UploadDesignHandler: metadane zapisane, design_id={saved.id}")

        # Publikuj event
        await publish_message(QUEUE_DESIGN_UPLOADED, {
            "design_id": saved.id,
            "order_id": saved.order_id,
            "filename": saved.filename,
            "extension": saved.extension,
            "file_size": saved.file_size,
            "s3_key": saved.s3_key,
        })
        logger.info(f"UploadDesignHandler: event opublikowany dla design_id={saved.id}")
        return saved.id


# ── QUERY HANDLERS ────────────────────────────────────────────────────────────

class GetDesignHandler(RequestHandler[GetDesignQuery, DesignFile]):
    """CQS: Query — pobiera metadane pliku z bazy."""
    def __init__(self, repo: DesignRepository):
        self.repo = repo

    async def handle(self, query: GetDesignQuery) -> DesignFile:
        logger.info(f"GetDesignHandler: design_id={query.design_id}")
        design = await self.repo.find_by_id(query.design_id)
        if not design:
            raise ValueError(f"Plik {query.design_id} nie istnieje")
        return design


class GetDownloadUrlHandler(RequestHandler[GetDownloadUrlQuery, dict]):
    """
    CQS: Query — generuje świeży presigned URL z S3.
    Nie modyfikuje niczego w bazie — tylko pyta S3 o URL.
    """
    def __init__(self, repo: DesignRepository):
        self.repo = repo

    async def handle(self, query: GetDownloadUrlQuery) -> dict:
        logger.info(f"GetDownloadUrlHandler: generuję URL dla design_id={query.design_id}")
        design = await self.repo.find_by_id(query.design_id)
        if not design:
            raise ValueError(f"Plik {query.design_id} nie istnieje")

        # Generuj świeży URL (stary mógł wygasnąć)
        url = await generate_presigned_url(design.s3_key, query.expiration_seconds)
        logger.info(f"GetDownloadUrlHandler: URL wygenerowany dla s3_key={design.s3_key}")
        return {
            "design_id": design.id,
            "filename": design.filename,
            "download_url": url,
            "expires_in_seconds": query.expiration_seconds,
        }


class ListDesignsHandler(RequestHandler[ListDesignsQuery, list]):
    """CQS: Query — zwraca listę plików (opcjonalnie filtrowaną po order_id)."""
    def __init__(self, repo: DesignRepository):
        self.repo = repo

    async def handle(self, query: ListDesignsQuery):
        if query.order_id:
            logger.info(f"ListDesignsHandler: order_id={query.order_id}")
            return await self.repo.find_by_order_id(query.order_id)
        logger.info("ListDesignsHandler: wszystkie pliki")
        return await self.repo.find_all()
