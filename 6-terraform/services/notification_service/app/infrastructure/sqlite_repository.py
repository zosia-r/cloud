import logging
from typing import List
import boto3
from botocore.exceptions import ClientError
from app.domain.models import Notification
from app.domain.repository import NotificationRepository
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class DynamoDBNotificationRepository(NotificationRepository):
    def __init__(self):
        self.table_name = os.getenv("DYNAMODB_NOTIFICATIONS_TABLE", "notifications")
        self.table = None
        
    async def init_connection(self):
        """Initialize DynamoDB connection and log result"""
        try:
            logger.info(f"Starting DynamoDB connection for NotificationService to table '{self.table_name}'")
            
            dynamodb = boto3.resource(
                'dynamodb',
                region_name=os.getenv("AWS_REGION", "us-east-1"),
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
            )
            
            self.table = dynamodb.Table(self.table_name)
            # Test connection by checking table status
            response = self.table.table_status
            logger.info(f"DynamoDB connection successful. Table status: {response}")
            
        except Exception as e:
            logger.error(f"DynamoDB connection failed: {str(e)}", exc_info=True)
            raise

    async def save(self, n: Notification) -> Notification:
        logger.info(f"save: notification id={n.id}, order_id={n.order_id}")
        try:
            self.table.put_item(Item={
                'id': n.id,
                'order_id': n.order_id,
                'recipient_email': n.recipient_email,
                'message': n.message,
                'notification_type': n.notification_type,
                'status': n.status,
                'created_at': n.created_at.isoformat()
            })
            logger.info(f"Notification saved successfully: id={n.id}")
            return n
        except ClientError as e:
            logger.error(f"Failed to save notification: {e}", exc_info=True)
            raise

    async def find_by_order_id(self, order_id: str) -> List[Notification]:
        logger.info(f"find_by_order_id: order_id={order_id}")
        try:
            response = self.table.query(KeyConditionExpression='order_id = :oid', 
                                       ExpressionAttributeValues={':oid': order_id})
            notifications = [self._item_to_notification(item) for item in response.get('Items', [])]
            logger.info(f"Found {len(notifications)} notifications for order_id={order_id}")
            return notifications
        except ClientError as e:
            logger.error(f"Failed to find notifications by order_id: {e}", exc_info=True)
            raise

    async def find_all(self) -> List[Notification]:
        logger.info("find_all: fetching all notifications")
        try:
            response = self.table.scan()
            notifications = [self._item_to_notification(item) for item in response.get('Items', [])]
            logger.info(f"Found {len(notifications)} total notifications")
            return notifications
        except ClientError as e:
            logger.error(f"Failed to fetch all notifications: {e}", exc_info=True)
            raise

    def _item_to_notification(self, item) -> Notification:
        return Notification(
            id=item['id'],
            order_id=item['order_id'],
            recipient_email=item['recipient_email'],
            message=item['message'],
            notification_type=item['notification_type'],
            status=item['status'],
            created_at=datetime.fromisoformat(item['created_at'])
        )


# Global instance
_notification_repo = None


async def init_db():
    """Initialize DynamoDB connection"""
    global _notification_repo
    try:
        logger.info("Initializing NotificationService DynamoDB connection")
        _notification_repo = DynamoDBNotificationRepository()
        await _notification_repo.init_connection()
        logger.info("NotificationService DynamoDB initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize DynamoDB: {str(e)}", exc_info=True)
        raise


def get_notification_repository() -> DynamoDBNotificationRepository:
    if _notification_repo is None:
        raise RuntimeError("Repository not initialized. Call init_db() first.")
    return _notification_repo
