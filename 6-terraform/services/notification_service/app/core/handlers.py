import logging
from diator.requests import RequestHandler
from app.domain.models import Notification, SendNotificationCommand, ListNotificationsQuery

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set to DEBUG for detailed logs

class SendNotificationHandler(RequestHandler[SendNotificationCommand, str]):
    def __init__(self, repo):
        self.repo = repo

    async def handle(self, command: SendNotificationCommand) -> str:
        logger.info(f"SendNotificationHandler: type={command.notification_type}, order_id={command.order_id}")
        n = Notification(order_id=command.order_id, recipient_email=command.recipient_email,
                         message=command.message, notification_type=command.notification_type)
        saved = await self.repo.save(n)
        logger.info(f"SendNotificationHandler: powiadomienie wysłane do {command.recipient_email}")
        return saved.id


class ListNotificationsHandler(RequestHandler[ListNotificationsQuery, list]):
    def __init__(self, repo):
        self.repo = repo
        logger.debug(f"ListNotificationsHandler initialized with repository: {type(repo).__name__} {id(repo)}")

    async def handle(self, query: ListNotificationsQuery):
        if query.order_id:
            return await self.repo.find_by_order_id(query.order_id)
        return await self.repo.find_all()
