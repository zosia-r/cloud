import uuid
import logging
from app.domain.models import Payment, PaymentStatus
from app.domain.repository import PaymentRepository
from app.infrastructure.rabbitmq import publish_message

logger = logging.getLogger(__name__)
QUEUE_PAYMENT_PROCESSED = "payment.processed"


class ProcessPaymentUseCase:
    def __init__(self, repo: PaymentRepository):
        self.repo = repo

    async def execute(self, order_id: str, amount: float, currency: str = "PLN") -> Payment:
        logger.info(f"ProcessPaymentUseCase: processing payment for order_id={order_id}, amount={amount} {currency}")

        payment = Payment(
            order_id=order_id,
            amount=amount,
            currency=currency,
            status=PaymentStatus.PENDING,
        )
        saved = await self.repo.save(payment)
        logger.info(f"ProcessPaymentUseCase: payment id={saved.id} created with status=pending")

        # Simulated payment authorization
        auth_code = f"AUTH-{str(uuid.uuid4())[:8].upper()}"
        updated = await self.repo.update_status(saved.id, PaymentStatus.AUTHORIZED, auth_code)
        logger.info(f"ProcessPaymentUseCase: payment id={saved.id} authorized with code={auth_code}")

        await publish_message(QUEUE_PAYMENT_PROCESSED, {
            "payment_id": updated.id,
            "order_id": updated.order_id,
            "amount": updated.amount,
            "currency": updated.currency,
            "status": updated.status,
            "authorization_code": updated.authorization_code,
        })
        logger.info(f"ProcessPaymentUseCase: PaymentEvent published for order_id={order_id}")
        return updated


class GetPaymentUseCase:
    def __init__(self, repo: PaymentRepository):
        self.repo = repo

    async def execute(self, order_id: str) -> Payment:
        logger.info(f"GetPaymentUseCase: fetching payment for order_id={order_id}")
        payment = await self.repo.find_by_order_id(order_id)
        if not payment:
            raise ValueError(f"Payment for order {order_id} not found")
        return payment


class ListPaymentsUseCase:
    def __init__(self, repo: PaymentRepository):
        self.repo = repo

    async def execute(self):
        logger.info("ListPaymentsUseCase: listing all payments")
        return await self.repo.find_all()
