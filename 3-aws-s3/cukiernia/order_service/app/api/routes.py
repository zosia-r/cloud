from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from mediator import Mediator
from app.core.commands.order_commands import CreateOrderCommand, UpdateOrderStatusCommand
from app.core.queries.order_queries import GetOrderQuery, ListOrdersQuery
from app.core.handlers import (
    CreateOrderHandler, UpdateOrderStatusHandler,
    GetOrderHandler, ListOrdersHandler
)
from app.infrastructure.sqlite_repository import SQLiteOrderRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/orders", tags=["orders"])


def get_mediator() -> Mediator:
    repo = SQLiteOrderRepository()
    m = Mediator()
    # Rejestracja command handlerów
    m.register_command(CreateOrderCommand, CreateOrderHandler(repo))
    m.register_command(UpdateOrderStatusCommand, UpdateOrderStatusHandler(repo))
    # Rejestracja query handlerów
    m.register_query(GetOrderQuery, GetOrderHandler(repo))
    m.register_query(ListOrdersQuery, ListOrdersHandler(repo))
    return m


class CreateOrderRequest(BaseModel):
    customer_name: str
    customer_email: str
    product_description: str
    quantity: int = 1


class UpdateStatusRequest(BaseModel):
    status: str


@router.post("/", status_code=201)
async def create_order(body: CreateOrderRequest):
    logger.info(f"POST /orders - customer={body.customer_email}")
    m = get_mediator()
    # send() = Command (modyfikuje stan)
    order_id = await m.send(CreateOrderCommand(
        customer_name=body.customer_name,
        customer_email=body.customer_email,
        product_description=body.product_description,
        quantity=body.quantity,
    ))
    return {"order_id": order_id, "status": "pending", "message": "Zamówienie utworzone"}


@router.get("/")
async def list_orders():
    logger.info("GET /orders")
    m = get_mediator()
    # query() = Query (tylko odczyt)
    orders = await m.query(ListOrdersQuery())
    return [
        {"id": o.id, "customer_name": o.customer_name,
         "customer_email": o.customer_email,
         "product_description": o.product_description,
         "quantity": o.quantity, "status": o.status,
         "created_at": o.created_at.isoformat()}
        for o in orders
    ]


@router.get("/{order_id}")
async def get_order(order_id: str):
    logger.info(f"GET /orders/{order_id}")
    try:
        m = get_mediator()
        order = await m.query(GetOrderQuery(order_id=order_id))
        return {"id": order.id, "customer_name": order.customer_name,
                "customer_email": order.customer_email,
                "product_description": order.product_description,
                "quantity": order.quantity, "status": order.status,
                "created_at": order.created_at.isoformat(),
                "updated_at": order.updated_at.isoformat()}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{order_id}/status")
async def update_status(order_id: str, body: UpdateStatusRequest):
    logger.info(f"PATCH /orders/{order_id}/status → {body.status}")
    try:
        m = get_mediator()
        await m.send(UpdateOrderStatusCommand(order_id=order_id, status=body.status))
        return {"id": order_id, "status": body.status, "message": "Status zaktualizowany"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
