from .client import LoRaClient

_client = None


def client():
    global _client

    if _client is None:
        _client = LoRaClient()

    return _client


def start():
    client().start()


def send(to_addr, payload):
    return client().send(to_addr, payload)


def stop():
    client().stop()
