import uuid, logging
from mediator import CommandHandler, QueryHandler, Mediator
from app.domain.models import Payment, PaymentStatus
from app.core.commands.payment_commands import ProcessPaymentCommand, GetPaymentByOrderQuery, ListPaymentsQuery
from app.infrastructure.sqlite_repository import SQLitePaymentRepository
from app.infrastructure.rabbitmq import publish_message

logger = logging.getLogger(__name__)


class ProcessPaymentHandler(CommandHandler):
    def __init__(self, repo):
        self.repo = repo

    async def handle(self, command: ProcessPaymentCommand) -> str:
        logger.info(f"ProcessPaymentHandler: order_id={command.order_id}, amount={command.amount}")
        payment = Payment(order_id=command.order_id, amount=command.amount, currency=command.currency)
        saved = await self.repo.save(payment)
        auth_code = f"AUTH-{str(uuid.uuid4())[:8].upper()}"
        await self.repo.update_status(saved.id, PaymentStatus.AUTHORIZED, auth_code)
        logger.info(f"ProcessPaymentHandler: payment id={saved.id}, auth_code={auth_code}")
        await publish_message("payment.processed", {
            "payment_id": saved.id, "order_id": command.order_id,
            "amount": command.amount, "currency": command.currency,
            "status": "authorized", "authorization_code": auth_code,
        })
        return saved.id


class GetPaymentByOrderHandler(QueryHandler):
    def __init__(self, repo):
        self.repo = repo

    async def handle(self, query: GetPaymentByOrderQuery):
        logger.info(f"GetPaymentByOrderHandler: order_id={query.order_id}")
        payment = await self.repo.find_by_order_id(query.order_id)
        if not payment:
            raise ValueError(f"Płatność dla zamówienia {query.order_id} nie istnieje")
        return payment


class ListPaymentsHandler(QueryHandler):
    def __init__(self, repo):
        self.repo = repo

    async def handle(self, query: ListPaymentsQuery):
        logger.info("ListPaymentsHandler")
        return await self.repo.find_all()
