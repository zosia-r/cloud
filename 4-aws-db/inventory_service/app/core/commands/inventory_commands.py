from dataclasses import dataclass
from diator.requests import Request


@dataclass(frozen=True)
class ReserveIngredientsCommand(Request):
    order_id: str
    quantity_multiplier: int = 1


@dataclass(frozen=True)
class ListIngredientsQuery(Request):
    pass


@dataclass(frozen=True)
class ListReservationsQuery(Request):
    order_id: str = None
