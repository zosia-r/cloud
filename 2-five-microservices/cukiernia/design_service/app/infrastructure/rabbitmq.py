import aio_pika
import os
import logging

logger = logging.getLogger(__name__)

RABBITMQ_URL = "amqps://lbjzkreb:fqegv2EgZVI9II3T10Oc-19oRRQK_JrY@kebnekaise.lmq.cloudamqp.com/lbjzkreb"


async def get_rabbitmq_connection():
    logger.info("Connecting to RabbitMQ at CloudAMQP")
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    logger.info("RabbitMQ connection established")
    return connection


async def publish_message(queue_name: str, message: dict):
    import json
    logger.info(f"Publishing message to queue: {queue_name}, payload: {message}")
    connection = await get_rabbitmq_connection()
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue(queue_name, durable=True)
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(message).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=queue.name,
        )
    logger.info(f"Message published successfully to {queue_name}")
