from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.models import Notification


class NotificationRepository(ABC):

    @abstractmethod
    async def save(self, notification: Notification) -> Notification:
        pass

    @abstractmethod
    async def find_by_order_id(self, order_id: str) -> List[Notification]:
        pass

    @abstractmethod
    async def find_all(self) -> List[Notification]:
        pass
