class Publisher:
    def __init__(self, client):
        self.client = client

    def relay(self, payload):
        self.client.publish(
            TOPIC_RELAY,
            payload,
        )