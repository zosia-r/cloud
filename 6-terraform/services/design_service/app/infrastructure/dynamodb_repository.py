import logging
from typing import List, Optional
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
from app.domain.models import DesignFile
from app.domain.repository import DesignRepository
import os

logger = logging.getLogger(__name__)


class DynamoDBDesignRepository(DesignRepository):
    def __init__(self):
        self.table_name = os.getenv("DESIGN_TABLE", "design_files")
        self.table = None
        
    async def init_connection(self):
        """Initialize DynamoDB connection and log result"""
        try:
            logger.info(f"Starting DynamoDB connection for DesignService to table '{self.table_name}'")
            
            dynamodb = boto3.resource(
                'dynamodb',
                region_name=os.getenv("AWS_REGION", "us-east-1"),
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                aws_session_token=os.getenv("AWS_SESSION_TOKEN")
            )
            
            self.table = dynamodb.Table(self.table_name)
            # Test connection by checking table status (optional - may fail due to IAM restrictions)
            try:
                response = self.table.table_status
                logger.info(f"DynamoDB connection successful. Table status: {response}")
            except ClientError as e:
                if 'AccessDenied' in str(e):
                    logger.warning(f"DynamoDB table access verification skipped due to IAM permissions: {str(e)}. Operations will be attempted anyway.")
                else:
                    logger.error(f"DynamoDB table verification failed: {str(e)}", exc_info=True)
                    raise
            logger.info(f"DesignService DynamoDB connection initialized (table: {self.table_name})")
            
        except Exception as e:
            logger.error(f"DynamoDB connection failed: {str(e)}", exc_info=True)
            raise

    async def save(self, design: DesignFile) -> DesignFile:
        logger.info(f"save: design id={design.id}, filename={design.filename}, s3_key={design.s3_key}")
        try:
            self.table.put_item(Item={
                'id': design.id,
                'order_id': design.order_id,
                'filename': design.filename,
                'extension': design.extension,
                'file_size': design.file_size,
                's3_key': design.s3_key,
                's3_url': design.s3_url,
                'uploaded_at': design.uploaded_at.isoformat()
            })
            logger.info(f"Design file saved successfully: id={design.id}")
            return design
        except ClientError as e:
            logger.error(f"Failed to save design file: {e}", exc_info=True)
            raise

    async def find_by_id(self, design_id: str) -> Optional[DesignFile]:
        logger.info(f"find_by_id: design_id={design_id}")
        try:
            response = self.table.get_item(Key={'id': design_id})
            if 'Item' in response:
                logger.info(f"Design file found: id={design_id}")
                return self._item_to_design(response['Item'])
            logger.info(f"Design file not found: id={design_id}")
            return None
        except ClientError as e:
            logger.error(f"Failed to find design file by id: {e}", exc_info=True)
            raise

    async def find_by_order_id(self, order_id: str) -> List[DesignFile]:
        logger.info(f"find_by_order_id: order_id={order_id}")
        try:
            response = self.table.query(
                KeyConditionExpression='order_id = :oid',
                ExpressionAttributeValues={':oid': order_id}
            )
            designs = [self._item_to_design(item) for item in response.get('Items', [])]
            logger.info(f"Found {len(designs)} design files for order_id={order_id}")
            return designs
        except ClientError as e:
            logger.error(f"Failed to find design files by order_id: {e}", exc_info=True)
            raise

    async def find_all(self) -> List[DesignFile]:
        logger.info("find_all: fetching all design files")
        try:
            response = self.table.scan()
            designs = [self._item_to_design(item) for item in response.get('Items', [])]
            logger.info(f"Found {len(designs)} total design files")
            return designs
        except ClientError as e:
            logger.error(f"Failed to fetch all design files: {e}", exc_info=True)
            raise

    def _item_to_design(self, item) -> DesignFile:
        return DesignFile(
            id=item['id'],
            order_id=item['order_id'],
            filename=item['filename'],
            extension=item['extension'],
            file_size=item['file_size'],
            s3_key=item['s3_key'],
            s3_url=item['s3_url'],
            uploaded_at=datetime.fromisoformat(item['uploaded_at'])
        )


# Global instance
_design_repo = None


async def init_db():
    """Initialize DynamoDB connection"""
    global _design_repo
    try:
        logger.info("Initializing DesignService DynamoDB connection")
        _design_repo = DynamoDBDesignRepository()
        await _design_repo.init_connection()
        logger.info("DesignService DynamoDB initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize DynamoDB: {str(e)}", exc_info=True)
        raise


def get_design_repository() -> DynamoDBDesignRepository:
    if _design_repo is None:
        raise RuntimeError("Repository not initialized. Call init_db() first.")
    return _design_repo
