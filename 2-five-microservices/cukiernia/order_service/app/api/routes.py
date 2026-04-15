from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
import logging
from app.core.use_cases import (
    CreateOrderUseCase, GetOrderUseCase,
    ListOrdersUseCase, UpdateOrderStatusUseCase
)
from app.infrastructure.sqlite_repository import SQLiteOrderRepository

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/orders", tags=["orders"])


def get_repo():
    return SQLiteOrderRepository()


class CreateOrderRequest(BaseModel):
    customer_name: str
    customer_email: str
    product_description: str
    quantity: int = 1


class UpdateStatusRequest(BaseModel):
    status: str


@router.post("/", status_code=201)
async def create_order(body: CreateOrderRequest, repo=Depends(get_repo)):
    logger.info(f"POST /orders - creating order for {body.customer_email}")
    uc = CreateOrderUseCase(repo)
    order = await uc.execute(
        body.customer_name, body.customer_email,
        body.product_description, body.quantity
    )
    return {"order_id": order.id, "status": order.status, "message": "Order created successfully"}


@router.get("/", response_model=List[dict])
async def list_orders(repo=Depends(get_repo)):
    logger.info("GET /orders - listing all orders")
    uc = ListOrdersUseCase(repo)
    orders = await uc.execute()
    return [
        {"id": o.id, "customer_name": o.customer_name, "customer_email": o.customer_email,
         "product_description": o.product_description, "quantity": o.quantity,
         "status": o.status, "created_at": o.created_at.isoformat()}
        for o in orders
    ]


@router.get("/{order_id}")
async def get_order(order_id: str, repo=Depends(get_repo)):
    logger.info(f"GET /orders/{order_id}")
    try:
        uc = GetOrderUseCase(repo)
        order = await uc.execute(order_id)
        return {"id": order.id, "customer_name": order.customer_name,
                "customer_email": order.customer_email,
                "product_description": order.product_description,
                "quantity": order.quantity, "status": order.status,
                "created_at": order.created_at.isoformat(),
                "updated_at": order.updated_at.isoformat()}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{order_id}/status")
async def update_status(order_id: str, body: UpdateStatusRequest, repo=Depends(get_repo)):
    logger.info(f"PATCH /orders/{order_id}/status - new status={body.status}")
    try:
        uc = UpdateOrderStatusUseCase(repo)
        order = await uc.execute(order_id, body.status)
        return {"id": order.id, "status": order.status, "message": "Status updated"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))