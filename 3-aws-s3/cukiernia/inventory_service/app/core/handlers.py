import logging
from mediator import CommandHandler, QueryHandler, Mediator
from app.domain.models import Reservation
from app.core.commands.inventory_commands import (
    ReserveIngredientsCommand, ListIngredientsQuery, ListReservationsQuery
)
from app.infrastructure.sqlite_repository import SQLiteIngredientRepository, SQLiteReservationRepository
from app.infrastructure.rabbitmq import publish_message

logger = logging.getLogger(__name__)

DEFAULT_INGREDIENTS = [
    {"name": "mąka", "quantity": 2.0},
    {"name": "cukier", "quantity": 1.0},
    {"name": "masło", "quantity": 0.5},
    {"name": "jajka", "quantity": 6.0},
]


class ReserveIngredientsHandler(CommandHandler):
    def __init__(self, ing_repo, res_repo):
        self.ing_repo = ing_repo
        self.res_repo = res_repo

    async def handle(self, command: ReserveIngredientsCommand):
        logger.info(f"ReserveIngredientsHandler: order_id={command.order_id}")
        reservations = []
        for item in DEFAULT_INGREDIENTS:
            needed = item["quantity"] * command.quantity_multiplier
            ingredient = await self.ing_repo.find_by_name(item["name"])
            if ingredient and ingredient.quantity >= needed:
                await self.ing_repo.update_quantity(item["name"], ingredient.quantity - needed)
                res = Reservation(order_id=command.order_id,
                                  ingredient_name=item["name"], quantity_reserved=needed)
                saved = await self.res_repo.save(res)
                reservations.append(saved)
                logger.info(f"Zarezerwowano {needed} {item['name']}")
        await publish_message("inventory.reserved", {
            "order_id": command.order_id,
            "reservations": [{"ingredient": r.ingredient_name, "quantity": r.quantity_reserved}
                             for r in reservations],
            "status": "reserved"
        })
        return command.order_id


class ListIngredientsHandler(QueryHandler):
    def __init__(self, repo):
        self.repo = repo

    async def handle(self, query: ListIngredientsQuery):
        logger.info("ListIngredientsHandler")
        return await self.repo.find_all()


class ListReservationsHandler(QueryHandler):
    def __init__(self, repo):
        self.repo = repo

    async def handle(self, query: ListReservationsQuery):
        logger.info(f"ListReservationsHandler: order_id={query.order_id}")
        if query.order_id:
            return await self.repo.find_by_order_id(query.order_id)
        return await self.repo.find_all()
