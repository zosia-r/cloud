"""
Mediator Pattern + CQS
-----------------------
Command  - modyfikuje stan, nie zwraca danych biznesowych
Query    - odczytuje stan, nie modyfikuje niczego
Mediator - przyjmuje Command lub Query i przekazuje do właściwego handlera
"""
from typing import Any, Dict, Type
import logging

logger = logging.getLogger(__name__)


class Command:
    """Bazowa klasa dla wszystkich komend (operacje zapisu)."""
    pass


class Query:
    """Bazowa klasa dla wszystkich zapytań (operacje odczytu)."""
    pass


class CommandHandler:
    """Bazowa klasa dla handlerów komend."""
    async def handle(self, command: Command) -> Any:
        raise NotImplementedError


class QueryHandler:
    """Bazowa klasa dla handlerów zapytań."""
    async def handle(self, query: Query) -> Any:
        raise NotImplementedError


class Mediator:
    """
    Pośrednik który:
    - rejestruje handlery dla komend i zapytań
    - kieruje komendy/zapytania do właściwych handlerów
    """

    def __init__(self):
        self._command_handlers: Dict[Type[Command], CommandHandler] = {}
        self._query_handlers: Dict[Type[Query], QueryHandler] = {}

    def register_command(self, command_type: Type[Command], handler: CommandHandler):
        logger.info(f"Mediator: rejestrowanie handlera dla komendy {command_type.__name__}")
        self._command_handlers[command_type] = handler

    def register_query(self, query_type: Type[Query], handler: QueryHandler):
        logger.info(f"Mediator: rejestrowanie handlera dla zapytania {query_type.__name__}")
        self._query_handlers[query_type] = handler

    async def send(self, command: Command) -> Any:
        handler = self._command_handlers.get(type(command))
        if not handler:
            raise ValueError(f"Brak handlera dla komendy: {type(command).__name__}")
        logger.info(f"Mediator: przekazuję komendę {type(command).__name__} do handlera")
        return await handler.handle(command)

    async def query(self, query: Query) -> Any:
        handler = self._query_handlers.get(type(query))
        if not handler:
            raise ValueError(f"Brak handlera dla zapytania: {type(query).__name__}")
        logger.info(f"Mediator: przekazuję zapytanie {type(query).__name__} do handlera")
        return await handler.handle(query)
