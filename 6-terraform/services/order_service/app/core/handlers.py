import logging
from diator.requests import RequestHandler
from app.domain.models import Order
from app.domain.repository import OrderRepository
from app.core.commands.order_commands import CreateOrderCommand, UpdateOrderStatusCommand
from app.core.queries.order_queries import GetOrderQuery, ListOrdersQuery
from app.infrastructure.rabbitmq import publish_message

logger = logging.getLogger(__name__)

QUEUE_ORDER_CREATED = "order.created"


# ── COMMAND HANDLERS ──────────────────────────────────────────────────────────

class CreateOrderHandler(RequestHandler[CreateOrderCommand, str]):
    """
    CQS: Command — modyfikuje stan (tworzy zamówienie w bazie, publikuje event).
    Nie zwraca danych biznesowych — zwraca tylko ID utworzonego zasobu.
    """
    def __init__(self, repo: OrderRepository):
        self.repo = repo

    async def handle(self, command: CreateOrderCommand) -> str:
        logger.info(f"CreateOrderHandler: tworzę zamówienie dla {command.customer_name}")
        order = Order(
            customer_name=command.customer_name,
            customer_email=command.customer_email,
            product_description=command.product_description,
            quantity=command.quantity,
        )
        saved = await self.repo.save(order)
        logger.info(f"CreateOrderHandler: zamówienie id={saved.id} zapisane")

        await publish_message(QUEUE_ORDER_CREATED, {
            "order_id": saved.id,
            "customer_name": saved.customer_name,
            "customer_email": saved.customer_email,
            "product_description": saved.product_description,
            "quantity": saved.quantity,
        })
        logger.info(f"CreateOrderHandler: event opublikowany dla order_id={saved.id}")
        return saved.id


class UpdateOrderStatusHandler(RequestHandler[UpdateOrderStatusCommand, str]):
    """
    CQS: Command — modyfikuje status zamówienia.
    """
    def __init__(self, repo: OrderRepository):
        self.repo = repo

    async def handle(self, command: UpdateOrderStatusCommand) -> str:
        logger.info(f"UpdateOrderStatusHandler: zmieniam status order_id={command.order_id} na {command.status}")
        order = await self.repo.update_status(command.order_id, command.status)
        if not order:
            raise ValueError(f"Zamówienie {command.order_id} nie istnieje")
        logger.info(f"UpdateOrderStatusHandler: status zaktualizowany")
        return order.id


# ── QUERY HANDLERS ────────────────────────────────────────────────────────────

class GetOrderHandler(RequestHandler[GetOrderQuery, Order]):
    """
    CQS: Query — tylko odczytuje, nic nie modyfikuje.
    """
    def __init__(self, repo: OrderRepository):
        self.repo = repo

    async def handle(self, query: GetOrderQuery) -> Order:
        logger.info(f"GetOrderHandler: pobieram order_id={query.order_id}")
        order = await self.repo.find_by_id(query.order_id)
        if not order:
            raise ValueError(f"Zamówienie {query.order_id} nie istnieje")
        return order


class ListOrdersHandler(RequestHandler[ListOrdersQuery, list]):
    """
    CQS: Query — zwraca listę wszystkich zamówień.
    """
    def __init__(self, repo: OrderRepository):
        self.repo = repo

    async def handle(self, query: ListOrdersQuery):
        logger.info("ListOrdersHandler: pobieram wszystkie zamówienia")
        return await self.repo.find_all()
