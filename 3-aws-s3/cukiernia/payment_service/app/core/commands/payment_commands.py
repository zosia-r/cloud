from mediator import Command, Query
from dataclasses import dataclass


@dataclass
class ProcessPaymentCommand(Command):
    order_id: str
    amount: float
    currency: str = "PLN"


@dataclass
class GetPaymentByOrderQuery(Query):
    order_id: str


@dataclass
class ListPaymentsQuery(Query):
    pass
