from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.models import Order


class OrderRepository(ABC):

    @abstractmethod
    async def save(self, order: Order) -> Order:
        pass

    @abstractmethod
    async def find_by_id(self, order_id: str) -> Optional[Order]:
        pass

    @abstractmethod
    async def find_all(self) -> List[Order]:
        pass

    @abstractmethod
    async def update_status(self, order_id: str, status: str) -> Optional[Order]:
        pass