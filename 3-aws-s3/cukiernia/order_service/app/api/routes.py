from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
from typing import Optional
from diator.mediator import Mediator
from diator.requests import RequestMap
from app.core.commands.order_commands import CreateOrderCommand, UpdateOrderStatusCommand
from app.core.queries.order_queries import GetOrderQuery, ListOrdersQuery
from app.core.handlers import (
    CreateOrderHandler, UpdateOrderStatusHandler,
    GetOrderHandler, ListOrdersHandler
)
from app.infrastructure.sqlite_repository import SQLiteOrderRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/orders", tags=["orders"])

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
    
    repo = SQLiteOrderRepository()
    
    # Create handler instances
    create_order_handler = CreateOrderHandler(repo)
    update_status_handler = UpdateOrderStatusHandler(repo)
    get_order_handler = GetOrderHandler(repo)
    list_orders_handler = ListOrdersHandler(repo)
    
    # Setup simple container with handler instances
    container = SimpleContainer({
        CreateOrderHandler: create_order_handler,
        UpdateOrderStatusHandler: update_status_handler,
        GetOrderHandler: get_order_handler,
        ListOrdersHandler: list_orders_handler,
    })
    
    # Setup request map
    request_map = RequestMap()
    request_map.bind(CreateOrderCommand, CreateOrderHandler)
    request_map.bind(UpdateOrderStatusCommand, UpdateOrderStatusHandler)
    request_map.bind(GetOrderQuery, GetOrderHandler)
    request_map.bind(ListOrdersQuery, ListOrdersHandler)
    
    # Create mediator
    _mediator = Mediator(
        request_map=request_map,
        container=container,
    )
    return _mediator


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
    mediator = get_mediator()
    # send() = Command/Request (modyfikuje stan)
    order_id = await mediator.send(CreateOrderCommand(
        customer_name=body.customer_name,
        customer_email=body.customer_email,
        product_description=body.product_description,
        quantity=body.quantity,
    ))
    return {"order_id": order_id, "status": "pending", "message": "Zamówienie utworzone"}


@router.get("/")
async def list_orders():
    logger.info("GET /orders")
    mediator = get_mediator()
    # send() = Query/Request (tylko odczyt)
    orders = await mediator.send(ListOrdersQuery())
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
        mediator = get_mediator()
        order = await mediator.send(GetOrderQuery(order_id=order_id))
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
        mediator = get_mediator()
        await mediator.send(UpdateOrderStatusCommand(order_id=order_id, status=body.status))
        return {"id": order_id, "status": body.status, "message": "Status zaktualizowany"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
