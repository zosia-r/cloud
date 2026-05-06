from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.models import Payment


class PaymentRepository(ABC):

    @abstractmethod
    async def save(self, payment: Payment) -> Payment:
        pass

    @abstractmethod
    async def find_by_id(self, payment_id: str) -> Optional[Payment]:
        pass

    @abstractmethod
    async def find_by_order_id(self, order_id: str) -> Optional[Payment]:
        pass

    @abstractmethod
    async def find_all(self) -> List[Payment]:
        pass

    @abstractmethod
    async def update_status(self, payment_id: str, status: str, auth_code: str = "") -> Optional[Payment]:
        pass
