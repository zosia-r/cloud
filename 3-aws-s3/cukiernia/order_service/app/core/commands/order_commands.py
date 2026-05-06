from mediator import Command
from dataclasses import dataclass


@dataclass
class CreateOrderCommand(Command):
    customer_name: str
    customer_email: str
    product_description: str
    quantity: int


@dataclass
class UpdateOrderStatusCommand(Command):
    order_id: str
    status: str
