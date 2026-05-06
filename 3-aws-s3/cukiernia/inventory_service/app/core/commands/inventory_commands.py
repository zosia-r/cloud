from mediator import Command, Query
from dataclasses import dataclass


@dataclass
class ReserveIngredientsCommand(Command):
    order_id: str
    quantity_multiplier: int = 1


@dataclass
class ListIngredientsQuery(Query):
    pass


@dataclass
class ListReservationsQuery(Query):
    order_id: str = None
