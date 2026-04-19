import logging
from app.domain.models import Order, OrderStatus
from app.domain.repository import OrderRepository
from app.infrastructure.rabbitmq import publish_message

logger = logging.getLogger(__name__)

QUEUE_ORDER_CREATED = "order.created"


class CreateOrderUseCase:
    def __init__(self, repo: OrderRepository):
        self.repo = repo

    async def execute(self, customer_name: str, customer_email: str,
                      product_description: str, quantity: int) -> Order:
        logger.info(f"CreateOrderUseCase: creating order for customer={customer_name}")
        order = Order(
            customer_name=customer_name,
            customer_email=customer_email,
            product_description=product_description,
            quantity=quantity,
        )
        saved_order = await self.repo.save(order)
        logger.info(f"CreateOrderUseCase: order id={saved_order.id} created with status=pending")

        await publish_message(QUEUE_ORDER_CREATED, {
            "order_id": saved_order.id,
            "customer_name": saved_order.customer_name,
            "customer_email": saved_order.customer_email,
            "product_description": saved_order.product_description,
            "quantity": saved_order.quantity,
        })
        logger.info(f"CreateOrderUseCase: OrderEvent published for order id={saved_order.id}")
        return saved_order


class GetOrderUseCase:
    def __init__(self, repo: OrderRepository):
        self.repo = repo

    async def execute(self, order_id: str) -> Order:
        logger.info(f"GetOrderUseCase: fetching order id={order_id}")
        order = await self.repo.find_by_id(order_id)
        if not order:
            logger.warning(f"GetOrderUseCase: order id={order_id} not found")
            raise ValueError(f"Order {order_id} not found")
        return order


class ListOrdersUseCase:
    def __init__(self, repo: OrderRepository):
        self.repo = repo

    async def execute(self):
        logger.info("ListOrdersUseCase: listing all orders")
        return await self.repo.find_all()


class UpdateOrderStatusUseCase:
    def __init__(self, repo: OrderRepository):
        self.repo = repo

    async def execute(self, order_id: str, status: str) -> Order:
        logger.info(f"UpdateOrderStatusUseCase: updating order id={order_id} to status={status}")
        order = await self.repo.update_status(order_id, status)
        if not order:
            raise ValueError(f"Order {order_id} not found")
        logger.info(f"UpdateOrderStatusUseCase: order id={order_id} updated to status={status}")
        return order
