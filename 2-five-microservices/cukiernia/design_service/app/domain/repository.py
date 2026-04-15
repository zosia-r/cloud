from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.models import DesignFile


class DesignRepository(ABC):

    @abstractmethod
    async def save(self, design: DesignFile) -> DesignFile:
        pass

    @abstractmethod
    async def find_by_order_id(self, order_id: str) -> List[DesignFile]:
        pass

    @abstractmethod
    async def find_all(self) -> List[DesignFile]:
        pass