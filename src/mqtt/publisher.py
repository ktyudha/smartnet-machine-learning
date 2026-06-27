from .publishers.status import publish as status_publish


class Publisher:
    def __init__(self, client):
        self.client = client

    def status(self, payload):
        status_publish(payload, self.client)
