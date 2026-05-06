from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import logging
from diator.mediator import Mediator
from diator.requests import RequestMap
from app.core.commands.inventory_commands import (
    ReserveIngredientsCommand, ListIngredientsQuery, ListReservationsQuery
)
from app.core.handlers import ReserveIngredientsHandler, ListIngredientsHandler, ListReservationsHandler
from app.infrastructure.sqlite_repository import SQLiteIngredientRepository, SQLiteReservationRepository

logger = logging.getLogger(__name__)
router = APIRouter(tags=["inventory"])

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
    
    ing_repo = SQLiteIngredientRepository()
    res_repo = SQLiteReservationRepository()
    
    # Create handler instances
    reserve_handler = ReserveIngredientsHandler(ing_repo, res_repo)
    list_ingredients_handler = ListIngredientsHandler(ing_repo)
    list_reservations_handler = ListReservationsHandler(res_repo)
    
    # Setup simple container with handler instances
    container = SimpleContainer({
        ReserveIngredientsHandler: reserve_handler,
        ListIngredientsHandler: list_ingredients_handler,
        ListReservationsHandler: list_reservations_handler,
    })
    
    # Setup request map
    request_map = RequestMap()
    request_map.bind(ReserveIngredientsCommand, ReserveIngredientsHandler)
    request_map.bind(ListIngredientsQuery, ListIngredientsHandler)
    request_map.bind(ListReservationsQuery, ListReservationsHandler)
    
    # Create mediator
    _mediator = Mediator(
        request_map=request_map,
        container=container,
    )
    return _mediator


class ReserveRequest(BaseModel):
    order_id: str
    quantity_multiplier: int = 1


@router.post("/reserve", status_code=201)
async def reserve(body: ReserveRequest):
    logger.info(f"POST /reserve - order_id={body.order_id}")
    mediator = get_mediator()
    await mediator.send(ReserveIngredientsCommand(order_id=body.order_id,
                                           quantity_multiplier=body.quantity_multiplier))
    reservations = await mediator.send(ListReservationsQuery(order_id=body.order_id))
    return {
        "order_id": body.order_id,
        "reserved_count": len(reservations),
        "reservations": [{"ingredient": r.ingredient_name, "quantity": r.quantity_reserved}
                         for r in reservations],
        "message": "Składniki zarezerwowane"
    }


@router.get("/ingredients")
async def list_ingredients():
    mediator = get_mediator()
    items = await mediator.send(ListIngredientsQuery())
    return [{"id": i.id, "name": i.name, "quantity": i.quantity, "unit": i.unit} for i in items]


@router.get("/reservations")
async def list_reservations(order_id: Optional[str] = None):
    mediator = get_mediator()
    items = await mediator.send(ListReservationsQuery(order_id=order_id))
    return [{"id": r.id, "order_id": r.order_id, "ingredient_name": r.ingredient_name,
             "quantity_reserved": r.quantity_reserved, "status": r.status} for r in items]
