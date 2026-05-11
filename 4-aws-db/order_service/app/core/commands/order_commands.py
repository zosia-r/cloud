from dataclasses import dataclass
from diator.requests import Request


@dataclass(frozen=True)
class CreateOrderCommand(Request):
    customer_name: str
    customer_email: str
    product_description: str
    quantity: int


@dataclass(frozen=True)
class UpdateOrderStatusCommand(Request):
    order_id: str
    status: str
