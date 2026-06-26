class Subscriber:

    def __init__(self, client):
        self.client = client

    def subscribe(self):

        self.client.subscribe(TOPIC_LINK_LOG)