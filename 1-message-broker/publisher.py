import json
import time
from base import MessageBroker

class Publisher(MessageBroker):
    def publish(self, event_instance):
        self.log_method("publish")
        channel_name = self.get_channel_name(event_instance.__class__)
        self.channel.queue_declare(queue=channel_name, durable=True, arguments={'x-queue-type': 'quorum'})
        
        body = json.dumps(event_instance.to_dict())
        self.channel.basic_publish(exchange='', routing_key=channel_name, body=body)
        self.logger.info(f"Published message to {channel_name}: {body}")