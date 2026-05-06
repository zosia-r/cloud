import aio_pika
import json
import logging
import asyncio
import os
from diator.mediator import Mediator
from diator.requests import RequestMap
from app.domain.models import SendNotificationCommand
from app.infrastructure.sqlite_repository import SQLiteNotificationRepository
from app.core.handlers import SendNotificationHandler

logger = logging.getLogger(__name__)
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqps://user:password@host/vhost")

TEMPLATES = {
    "order.created": ("order_created",
        lambda d: (d.get("customer_email", "client@example.com"),
                   f"Zamówienie #{d.get('order_id','?')} przyjęte. Produkt: {d.get('product_description','')}")),
    "design.uploaded": ("design_uploaded",
        lambda d: ("client@example.com",
                   f"Plik '{d.get('filename','?')}' (.{d.get('extension','?')}) odebrany dla zamówienia #{d.get('order_id','?')}")),
    "inventory.reserved": ("inventory_reserved",
        lambda d: ("client@example.com",
                   f"Składniki dla zamówienia #{d.get('order_id','?')} zarezerwowane.")),
    "payment.processed": ("payment_processed",
        lambda d: ("client@example.com",
                   f"Płatność dla #{d.get('order_id','?')} autoryzowana. Kod: {d.get('authorization_code','N/A')}")),
}

# Simple container for handler instances
class SimpleContainer:
    def __init__(self, handlers_map: dict):
        self.handlers = handlers_map
    
    async def resolve(self, handler_type):
        return self.handlers.get(handler_type)

def create_mediator(repo):
    """Tworzy Mediator z diator"""
    handler = SendNotificationHandler(repo)
    container = SimpleContainer({SendNotificationHandler: handler})
    request_map = RequestMap()
    request_map.bind(SendNotificationCommand, SendNotificationHandler)
    return Mediator(request_map=request_map, container=container)


async def start_consumer():
    logger.info("NotificationService: łączenie z RabbitMQ")
    try:
        connection = await asyncio.wait_for(
            aio_pika.connect_robust(RABBITMQ_URL),
            timeout=5.0
        )
    except asyncio.TimeoutError:
        logger.error("Timeout przy łączeniu z RabbitMQ - consumer nie będzie działać")
        raise
    except Exception as e:
        logger.error(f"Błąd połączenia z RabbitMQ: {e}")
        raise

    channel = await connection.channel()
    await channel.set_qos(prefetch_count=10)
    repo = SQLiteNotificationRepository()

    for queue_name in TEMPLATES.keys():
        queue = await channel.declare_queue(queue_name, durable=True)

        async def make_handler(qname):
            async def handler(message: aio_pika.IncomingMessage):
                async with message.process():
                    try:
                        data = json.loads(message.body.decode())
                        logger.info(f"Odebrano wiadomość z queue={qname}: {data}")
                        notif_type, resolver = TEMPLATES[qname]
                        email, text = resolver(data)
                        cmd = SendNotificationCommand(
                            order_id=data.get("order_id", "unknown"),
                            recipient_email=email, message=text,
                            notification_type=notif_type)
                        m = create_mediator(repo)
                        await m.send(cmd)
                    except Exception as e:
                        logger.error(f"Błąd przetwarzania wiadomości z {qname}: {e}")
            return handler

        await queue.consume(await make_handler(queue_name))
        logger.info(f"Subskrybuję kolejkę: {queue_name}")

    logger.info("NotificationService consumer uruchomiony - nasłuchiwanie wiadomości")
    
    try:
        await asyncio.sleep(float('inf'))
    except asyncio.CancelledError:
        logger.info("Consumer anulowany")
        await connection.close()
        raise
