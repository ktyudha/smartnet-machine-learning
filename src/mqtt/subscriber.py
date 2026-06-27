from .subscribers.uplink import subscribe as uplink_subscribe
from .subscribers.downlink import subscribe as downlink_subscribe

from .topics import (
    UPLINK_TOPIC,
    DOWNLINK_TOPIC,
)


class Subscriber:
    def __init__(self, client):
        self.client = client
        self.handlers = {
            UPLINK_TOPIC: uplink_subscribe,
            DOWNLINK_TOPIC: downlink_subscribe,
        }

    def topics(self):
        return self.handlers.keys()

    def dispatch(self, topic: str, payload: str):
        handler = self.handlers.get(topic)
        if handler:
            handler(payload, self.client)
