import aio_pika
import json
import logging
import os
from app.domain.models import Notification
from app.infrastructure.sqlite_repository import SQLiteNotificationRepository

logger = logging.getLogger(__name__)

RABBITMQ_URL = "amqps://lbjzkreb:fqegv2EgZVI9II3T10Oc-19oRRQK_JrY@kebnekaise.lmq.cloudamqp.com/lbjzkreb"

QUEUES = [
    "order.created",
    "design.uploaded",
    "inventory.reserved",
    "payment.processed",
]

TEMPLATES = {
    "order.created": (
        "order_created",
        lambda data: (
            data.get("customer_email", "unknown@example.com"),
            f"Zamówienie #{data.get('order_id','?')} zostało przyjęte. "
            f"Produkt: {data.get('product_description','')}, ilość: {data.get('quantity',1)}."
        )
    ),
    "design.uploaded": (
        "design_uploaded",
        lambda data: (
            "client@example.com",
            f"Plik graficzny '{data.get('filename','?')}' "
            f"(.{data.get('extension','?')}) został odebrany dla zamówienia #{data.get('order_id','?')}."
        )
    ),
    "inventory.reserved": (
        "inventory_reserved",
        lambda data: (
            "client@example.com",
            f"Składniki dla zamówienia #{data.get('order_id','?')} zostały zarezerwowane. "
            f"Liczba pozycji: {len(data.get('reservations', []))}."
        )
    ),
    "payment.processed": (
        "payment_processed",
        lambda data: (
            "client@example.com",
            f"Płatność dla zamówienia #{data.get('order_id','?')} została autoryzowana. "
            f"Kwota: {data.get('amount',0)} {data.get('currency','PLN')}. "
            f"Kod autoryzacji: {data.get('authorization_code','N/A')}."
        )
    ),
}


async def start_consumer():
    logger.info("NotificationService: connecting to RabbitMQ to start consuming")
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=10)

    repo = SQLiteNotificationRepository()

    for queue_name in QUEUES:
        queue = await channel.declare_queue(queue_name, durable=True)

        async def make_handler(qname):
            async def handler(message: aio_pika.IncomingMessage):
                async with message.process():
                    try:
                        data = json.loads(message.body.decode())
                        logger.info(f"Received message from queue={qname}: {data}")

                        template = TEMPLATES.get(qname)
                        if not template:
                            logger.warning(f"No template for queue={qname}")
                            return

                        notif_type, resolver = template
                        recipient_email, msg_text = resolver(data)

                        notification = Notification(
                            order_id=data.get("order_id", "unknown"),
                            recipient_email=recipient_email,
                            message=msg_text,
                            notification_type=notif_type,
                            status="sent",
                        )
                        await repo.save(notification)
                        logger.info(
                            f"Notification sent to {recipient_email} "
                            f"[type={notif_type}] for order_id={notification.order_id}"
                        )
                    except Exception as e:
                        logger.error(f"Error processing message from {qname}: {e}")
            return handler

        await queue.consume(await make_handler(queue_name))
        logger.info(f"NotificationService: subscribed to queue={queue_name}")

    logger.info("NotificationService: consumer running, waiting for messages...")
    return connection
