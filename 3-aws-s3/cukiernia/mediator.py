"""
Mediator Pattern + CQS using Diator
------------------------------------
Using Diator library for CQRS pattern implementation.
Command  - modyfikuje stan, nie zwraca danych biznesowych
Query    - odczytuje stan, nie modyfikuje niczego
"""
from diator import Command, Query, CommandHandler, QueryHandler
import logging

logger = logging.getLogger(__name__)

__all__ = ["Command", "Query", "CommandHandler", "QueryHandler"]
