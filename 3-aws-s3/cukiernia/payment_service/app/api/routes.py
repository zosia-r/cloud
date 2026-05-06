from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from mediator import Mediator
from app.core.commands.payment_commands import ProcessPaymentCommand, GetPaymentByOrderQuery, ListPaymentsQuery
from app.core.handlers import ProcessPaymentHandler, GetPaymentByOrderHandler, ListPaymentsHandler
from app.infrastructure.sqlite_repository import SQLitePaymentRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payments", tags=["payments"])


def get_mediator():
    repo = SQLitePaymentRepository()
    m = Mediator()
    m.register_command(ProcessPaymentCommand, ProcessPaymentHandler(repo))
    m.register_query(GetPaymentByOrderQuery, GetPaymentByOrderHandler(repo))
    m.register_query(ListPaymentsQuery, ListPaymentsHandler(repo))
    return m


class PaymentRequest(BaseModel):
    order_id: str
    amount: float
    currency: str = "PLN"


@router.post("/", status_code=201)
async def process_payment(body: PaymentRequest):
    logger.info(f"POST /payments - order_id={body.order_id}")
    m = get_mediator()
    payment_id = await m.send(ProcessPaymentCommand(order_id=body.order_id,
                                                     amount=body.amount, currency=body.currency))
    payment = await m.query(GetPaymentByOrderQuery(order_id=body.order_id))
    return {"payment_id": payment.id, "order_id": payment.order_id,
            "amount": payment.amount, "currency": payment.currency,
            "status": payment.status, "authorization_code": payment.authorization_code,
            "message": "Płatność autoryzowana"}


@router.get("/order/{order_id}")
async def get_payment(order_id: str):
    try:
        m = get_mediator()
        p = await m.query(GetPaymentByOrderQuery(order_id=order_id))
        return {"payment_id": p.id, "order_id": p.order_id, "amount": p.amount,
                "currency": p.currency, "status": p.status,
                "authorization_code": p.authorization_code}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/")
async def list_payments():
    m = get_mediator()
    payments = await m.query(ListPaymentsQuery())
    return [{"payment_id": p.id, "order_id": p.order_id, "amount": p.amount,
             "status": p.status, "authorization_code": p.authorization_code} for p in payments]
