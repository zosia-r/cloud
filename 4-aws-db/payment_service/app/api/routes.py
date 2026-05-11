from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from typing import Optional
from diator.mediator import Mediator
from diator.requests import RequestMap
from di import Container as DILibContainer
from di.dependent import Dependent
from app.core.commands.payment_commands import ProcessPaymentCommand, GetPaymentByOrderQuery, ListPaymentsQuery
from app.core.handlers import ProcessPaymentHandler, GetPaymentByOrderHandler, ListPaymentsHandler
from app.infrastructure.rds_repository import RDSPaymentRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payments", tags=["payments"])

# Singleton mediator instance
_mediator: Optional[Mediator] = None

# Simple container for handler instances
class SimpleContainer:
    def __init__(self, handlers_map: dict):
        self.handlers = handlers_map
    
    async def resolve(self, handler_type):
        return self.handlers.get(handler_type)

def get_mediator() -> Mediator:
    global _mediator
    if _mediator is not None:
        return _mediator
    
    repo = RDSPaymentRepository()
    
    # Create handler instances
    process_handler = ProcessPaymentHandler(repo)
    get_payment_handler = GetPaymentByOrderHandler(repo)
    list_payments_handler = ListPaymentsHandler(repo)
    
    # Setup simple container with handler instances
    container = SimpleContainer({
        ProcessPaymentHandler: process_handler,
        GetPaymentByOrderHandler: get_payment_handler,
        ListPaymentsHandler: list_payments_handler,
    })
    
    # Setup request map
    request_map = RequestMap()
    request_map.bind(ProcessPaymentCommand, ProcessPaymentHandler)
    request_map.bind(GetPaymentByOrderQuery, GetPaymentByOrderHandler)
    request_map.bind(ListPaymentsQuery, ListPaymentsHandler)
    
    # Create mediator
    _mediator = Mediator(
        request_map=request_map,
        container=container,
    )
    return _mediator


class PaymentRequest(BaseModel):
    order_id: str
    amount: float
    currency: str = "PLN"


@router.post("/", status_code=201)
async def process_payment(body: PaymentRequest):
    logger.info(f"POST /payments - order_id={body.order_id}")
    mediator = get_mediator()
    payment_id = await mediator.send(ProcessPaymentCommand(order_id=body.order_id,
                                                     amount=body.amount, currency=body.currency))
    payment = await mediator.send(GetPaymentByOrderQuery(order_id=body.order_id))
    return {"payment_id": payment.id, "order_id": payment.order_id,
            "amount": payment.amount, "currency": payment.currency,
            "status": payment.status, "authorization_code": payment.authorization_code,
            "message": "Płatność autoryzowana"}


@router.get("/order/{order_id}")
async def get_payment(order_id: str):
    try:
        mediator = get_mediator()
        p = await mediator.send(GetPaymentByOrderQuery(order_id=order_id))
        return {"payment_id": p.id, "order_id": p.order_id, "amount": p.amount,
                "currency": p.currency, "status": p.status,
                "authorization_code": p.authorization_code}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/")
async def list_payments():
    mediator = get_mediator()
    payments = await mediator.send(ListPaymentsQuery())
    return [{"payment_id": p.id, "order_id": p.order_id, "amount": p.amount,
             "status": p.status, "authorization_code": p.authorization_code} for p in payments]
