from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import logging
from mediator import Mediator
from app.core.commands.inventory_commands import (
    ReserveIngredientsCommand, ListIngredientsQuery, ListReservationsQuery
)
from app.core.handlers import ReserveIngredientsHandler, ListIngredientsHandler, ListReservationsHandler
from app.infrastructure.sqlite_repository import SQLiteIngredientRepository, SQLiteReservationRepository

logger = logging.getLogger(__name__)
router = APIRouter(tags=["inventory"])


def get_mediator():
    ing_repo = SQLiteIngredientRepository()
    res_repo = SQLiteReservationRepository()
    m = Mediator()
    m.register_command(ReserveIngredientsCommand, ReserveIngredientsHandler(ing_repo, res_repo))
    m.register_query(ListIngredientsQuery, ListIngredientsHandler(ing_repo))
    m.register_query(ListReservationsQuery, ListReservationsHandler(res_repo))
    return m


class ReserveRequest(BaseModel):
    order_id: str
    quantity_multiplier: int = 1


@router.post("/reserve", status_code=201)
async def reserve(body: ReserveRequest):
    logger.info(f"POST /reserve - order_id={body.order_id}")
    m = get_mediator()
    await m.send(ReserveIngredientsCommand(order_id=body.order_id,
                                           quantity_multiplier=body.quantity_multiplier))
    reservations = await m.query(ListReservationsQuery(order_id=body.order_id))
    return {
        "order_id": body.order_id,
        "reserved_count": len(reservations),
        "reservations": [{"ingredient": r.ingredient_name, "quantity": r.quantity_reserved}
                         for r in reservations],
        "message": "Składniki zarezerwowane"
    }


@router.get("/ingredients")
async def list_ingredients():
    m = get_mediator()
    items = await m.query(ListIngredientsQuery())
    return [{"id": i.id, "name": i.name, "quantity": i.quantity, "unit": i.unit} for i in items]


@router.get("/reservations")
async def list_reservations(order_id: Optional[str] = None):
    m = get_mediator()
    items = await m.query(ListReservationsQuery(order_id=order_id))
    return [{"id": r.id, "order_id": r.order_id, "ingredient_name": r.ingredient_name,
             "quantity_reserved": r.quantity_reserved, "status": r.status} for r in items]
