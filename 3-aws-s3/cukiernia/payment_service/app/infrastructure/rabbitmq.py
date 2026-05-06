import aio_pika, os, logging, json, asyncio
logger = logging.getLogger(__name__)
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqps://user:password@host/vhost")
logger.info(f"PaymentService RabbitMQ: URL={RABBITMQ_URL[:50]}...")

async def publish_message(queue_name: str, message: dict):
    logger.info(f"publish_message: queue={queue_name}")
    try:
        connection = await asyncio.wait_for(
            aio_pika.connect_robust(RABBITMQ_URL),
            timeout=10.0
        )
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue(queue_name, durable=True)
            await channel.default_exchange.publish(
                aio_pika.Message(body=json.dumps(message).encode(),
                                 delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
                routing_key=queue.name)
        logger.info(f"publish_message: opublikowano do {queue_name}")
    except asyncio.TimeoutError:
        logger.warning(f"publish_message: timeout RabbitMQ")
    except Exception as e:
        logger.warning(f"publish_message: error {queue_name}: {e}")
