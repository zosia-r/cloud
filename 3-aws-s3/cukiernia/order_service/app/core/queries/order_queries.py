from mediator import Query
from dataclasses import dataclass
from typing import Optional


@dataclass
class GetOrderQuery(Query):
    order_id: str


@dataclass
class ListOrdersQuery(Query):
    pass
