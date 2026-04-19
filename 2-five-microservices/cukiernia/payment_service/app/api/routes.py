from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import logging
from app.core.use_cases import ProcessPaymentUseCase, GetPaymentUseCase, ListPaymentsUseCase
from app.infrastructure.sqlite_repository import SQLitePaymentRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payments", tags=["payments"])


def get_repo():
    return SQLitePaymentRepository()


class PaymentRequest(BaseModel):
    order_id: str
    amount: float
    currency: str = "PLN"


@router.post("/", status_code=201)
async def process_payment(body: PaymentRequest, repo=Depends(get_repo)):
    logger.info(f"POST /payments - order_id={body.order_id}, amount={body.amount}")
    uc = ProcessPaymentUseCase(repo)
    payment = await uc.execute(body.order_id, body.amount, body.currency)
    return {
        "payment_id": payment.id,
        "order_id": payment.order_id,
        "amount": payment.amount,
        "currency": payment.currency,
        "status": payment.status,
        "authorization_code": payment.authorization_code,
        "message": "Payment processed and authorized"
    }


@router.get("/order/{order_id}")
async def get_payment_by_order(order_id: str, repo=Depends(get_repo)):
    logger.info(f"GET /payments/order/{order_id}")
    try:
        uc = GetPaymentUseCase(repo)
        payment = await uc.execute(order_id)
        return {
            "payment_id": payment.id,
            "order_id": payment.order_id,
            "amount": payment.amount,
            "currency": payment.currency,
            "status": payment.status,
            "authorization_code": payment.authorization_code,
            "created_at": payment.created_at.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/")
async def list_payments(repo=Depends(get_repo)):
    logger.info("GET /payments")
    uc = ListPaymentsUseCase(repo)
    payments = await uc.execute()
    return [
        {"payment_id": p.id, "order_id": p.order_id, "amount": p.amount,
         "currency": p.currency, "status": p.status,
         "authorization_code": p.authorization_code,
         "created_at": p.created_at.isoformat()}
        for p in payments
    ]
