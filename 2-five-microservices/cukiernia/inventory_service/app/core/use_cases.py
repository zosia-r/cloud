import logging
from typing import List
from app.domain.models import Reservation
from app.domain.repository import IngredientRepository, ReservationRepository
from app.infrastructure.rabbitmq import publish_message

logger = logging.getLogger(__name__)
QUEUE_INVENTORY_RESERVED = "inventory.reserved"

DEFAULT_INGREDIENTS = [
    {"name": "mąka", "quantity": 2.0},
    {"name": "cukier", "quantity": 1.0},
    {"name": "masło", "quantity": 0.5},
    {"name": "jajka", "quantity": 6.0},
]


class ReserveIngredientsUseCase:
    def __init__(self, ing_repo: IngredientRepository, res_repo: ReservationRepository):
        self.ing_repo = ing_repo
        self.res_repo = res_repo

    async def execute(self, order_id: str, quantity_multiplier: int = 1) -> List[Reservation]:
        logger.info(f"ReserveIngredientsUseCase: reserving ingredients for order_id={order_id}, multiplier={quantity_multiplier}")
        reservations = []
        for item in DEFAULT_INGREDIENTS:
            needed = item["quantity"] * quantity_multiplier
            ingredient = await self.ing_repo.find_by_name(item["name"])
            if ingredient and ingredient.quantity >= needed:
                new_qty = ingredient.quantity - needed
                await self.ing_repo.update_quantity(item["name"], new_qty)
                reservation = Reservation(
                    order_id=order_id,
                    ingredient_name=item["name"],
                    quantity_reserved=needed,
                    status="reserved"
                )
                saved = await self.res_repo.save(reservation)
                reservations.append(saved)
                logger.info(f"Reserved {needed} {item['name']} for order_id={order_id}")
            else:
                logger.warning(f"Insufficient stock for {item['name']}: needed={needed}")

        await publish_message(QUEUE_INVENTORY_RESERVED, {
            "order_id": order_id,
            "reservations": [
                {"ingredient": r.ingredient_name, "quantity": r.quantity_reserved}
                for r in reservations
            ],
            "status": "reserved"
        })
        logger.info(f"ReserveIngredientsUseCase: InventoryEvent published for order_id={order_id}")
        return reservations


class ListIngredientsUseCase:
    def __init__(self, repo: IngredientRepository):
        self.repo = repo

    async def execute(self):
        logger.info("ListIngredientsUseCase: listing all ingredients")
        return await self.repo.find_all()


class ListReservationsUseCase:
    def __init__(self, repo: ReservationRepository):
        self.repo = repo

    async def execute(self, order_id: str = None):
        if order_id:
            logger.info(f"ListReservationsUseCase: listing reservations for order_id={order_id}")
            return await self.repo.find_by_order_id(order_id)
        logger.info("ListReservationsUseCase: listing all reservations")
        return await self.repo.find_all()
