import json
from message_broker import MessageBroker

class Consumer(MessageBroker):
    def consume(self, event_class, callback):
        self.log_method("consume")
        channel_name = self.get_channel_name(event_class)
        self.channel.queue_declare(queue=channel_name, durable=True, arguments={'x-queue-type': 'quorum'})
        
        def internal_callback(ch, method, properties, body):
            data = json.loads(body)
            self.logger.info(f"Received message in {channel_name}: {data}")
            event = event_class.from_dict(data)
            callback(event)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        
        self.channel.basic_consume(queue=channel_name, on_message_callback=internal_callback)
        self.logger.info(f"Waiting for messages in {channel_name}")
        self.channel.start_consuming()