from dataclasses import dataclass
from typing import Optional
from diator.requests import Request


@dataclass(frozen=True)
class GetOrderQuery(Request):
    order_id: str


@dataclass(frozen=True)
class ListOrdersQuery(Request):
    pass
