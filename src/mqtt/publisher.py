from .publishers.status import publish as status_publish
from .publishers.uplink import publish as uplink_publish


class Publisher:
    def __init__(self, client):
        self.client = client

    def status(self, payload):
        status_publish(payload, self.client)

    def uplink(self, payload):
        uplink_publish(payload, self.client)
