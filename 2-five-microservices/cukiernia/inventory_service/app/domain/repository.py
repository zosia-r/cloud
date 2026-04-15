from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.models import Ingredient, Reservation


class IngredientRepository(ABC):

    @abstractmethod
    async def save(self, ingredient: Ingredient) -> Ingredient:
        pass

    @abstractmethod
    async def find_all(self) -> List[Ingredient]:
        pass

    @abstractmethod
    async def find_by_name(self, name: str) -> Optional[Ingredient]:
        pass

    @abstractmethod
    async def update_quantity(self, name: str, quantity: float) -> Optional[Ingredient]:
        pass


class ReservationRepository(ABC):

    @abstractmethod
    async def save(self, reservation: Reservation) -> Reservation:
        pass

    @abstractmethod
    async def find_by_order_id(self, order_id: str) -> List[Reservation]:
        pass

    @abstractmethod
    async def find_all(self) -> List[Reservation]:
        pass