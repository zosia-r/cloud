from dataclasses import dataclass
from diator.requests import Request


@dataclass(frozen=True)
class ProcessPaymentCommand(Request):
    order_id: str
    amount: float
    currency: str = "PLN"


@dataclass(frozen=True)
class GetPaymentByOrderQuery(Request):
    order_id: str


@dataclass(frozen=True)
class ListPaymentsQuery(Request):
    pass
