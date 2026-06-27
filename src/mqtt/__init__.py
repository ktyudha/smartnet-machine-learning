from . import topics

from .client import MQTTClient

_client = None


def client():
    global _client

    if _client is None:
        _client = MQTTClient()

    return _client


def start():
    client().start()


def publish(topic, payload):
    client().publish(topic, payload)


def publish_status(payload):
    client().publisher.status(payload)


def stop():
    client().stop()