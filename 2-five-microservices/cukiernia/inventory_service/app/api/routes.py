from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import logging
from app.core.use_cases import ReserveIngredientsUseCase, ListIngredientsUseCase, ListReservationsUseCase
from app.infrastructure.sqlite_repository import SQLiteIngredientRepository, SQLiteReservationRepository

logger = logging.getLogger(__name__)
router = APIRouter(tags=["inventory"])


def get_repos():
    return SQLiteIngredientRepository(), SQLiteReservationRepository()


class ReserveRequest(BaseModel):
    order_id: str
    quantity_multiplier: int = 1


@router.post("/reserve", status_code=201)
async def reserve_ingredients(body: ReserveRequest):
    logger.info(f"POST /reserve - order_id={body.order_id}")
    ing_repo, res_repo = get_repos()
    uc = ReserveIngredientsUseCase(ing_repo, res_repo)
    reservations = await uc.execute(body.order_id, body.quantity_multiplier)
    return {
        "order_id": body.order_id,
        "reserved_count": len(reservations),
        "reservations": [
            {"ingredient": r.ingredient_name, "quantity": r.quantity_reserved, "status": r.status}
            for r in reservations
        ],
        "message": "Ingredients reserved successfully"
    }


@router.get("/ingredients")
async def list_ingredients():
    logger.info("GET /ingredients")
    ing_repo, _ = get_repos()
    uc = ListIngredientsUseCase(ing_repo)
    items = await uc.execute()
    return [
        {"id": i.id, "name": i.name, "quantity": i.quantity, "unit": i.unit}
        for i in items
    ]


@router.get("/reservations")
async def list_reservations(order_id: Optional[str] = None):
    logger.info(f"GET /reservations - order_id={order_id}")
    _, res_repo = get_repos()
    uc = ListReservationsUseCase(res_repo)
    items = await uc.execute(order_id)
    return [
        {"id": r.id, "order_id": r.order_id, "ingredient_name": r.ingredient_name,
         "quantity_reserved": r.quantity_reserved, "status": r.status,
         "created_at": r.created_at.isoformat()}
        for r in items
    ]