import time
import random
import multiprocessing
import sys
import logging

from events import Type1Event, Type2Event, Type3Event, Type4Event
from publisher import Publisher
from consumer import Consumer

AMQP_URL = 'amqps://kptvgblb:TNtpjZI47qf5ksO1iWbnveWYqQpfAYAw@kebnekaise.lmq.cloudamqp.com/kptvgblb'

logger = logging.getLogger("Main")
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] -- %(message)s')

def run_pub(event_class, interval=None):
    try:
        pub = Publisher(AMQP_URL)
        while True:
            pub.publish(event_class())
            time.sleep(interval if interval else random.randint(1, 5))
    except KeyboardInterrupt:
        pub.close()

def run_cons(event_class):
    try:
        cons = Consumer(AMQP_URL)
        cons.consume(event_class, lambda d: None)
    except KeyboardInterrupt:
        cons.close()

def run_cons_3_to_4():
    try:
        cons = Consumer(AMQP_URL)
        pub = Publisher(AMQP_URL)
        def callback(event):
            pub.publish(Type4Event(f"Processed {event.message}"))
        cons.consume(Type3Event, callback)
    except KeyboardInterrupt:
        pub.close()
        cons.close()


if __name__ == "__main__":
    processes = [
        # Type 1
        multiprocessing.Process(target=run_pub, args=(Type1Event, 3)),
        multiprocessing.Process(target=run_pub, args=(Type1Event, 3)),
        multiprocessing.Process(target=run_pub, args=(Type1Event, 3)),
        # Type 2, Type 3
        multiprocessing.Process(target=run_pub, args=(Type2Event,)),
        multiprocessing.Process(target=run_pub, args=(Type3Event,)),
        # Consumers
        multiprocessing.Process(target=run_cons, args=(Type1Event,)),
        multiprocessing.Process(target=run_cons, args=(Type1Event,)),
        multiprocessing.Process(target=run_cons, args=(Type2Event,)),
        multiprocessing.Process(target=run_cons_3_to_4, args=()), # Type 3 -> 4
        multiprocessing.Process(target=run_cons, args=(Type4Event,)),
    ]

    logger.info("Starting processes...")
    
    for p in processes:
        p.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        for p in processes:
            p.terminate()
            p.join()
        sys.exit(0)