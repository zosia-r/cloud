import pika
import logging

logging.basicConfig(level=logging.INFO, 
                    format='[%(levelname)s] -- %(message)s')
logging.getLogger('pika').setLevel(logging.WARNING)  # Suppress pika logs

class MessageBroker:
    def __init__(self, amqp_url):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.connection = pika.BlockingConnection(pika.URLParameters(amqp_url))
        self.channel = self.connection.channel()
        self.logger.info("Connected to RabbitMQ")
    
    def get_channel_name(self, event_class):
        return event_class.__name__
    
    def log_method(self, method_name):
        self.logger.info(f"Executing method: {method_name}")

    def close(self):
        self.log_method("close")
        self.connection.close()