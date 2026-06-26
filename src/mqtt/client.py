import json
import logging

import paho.mqtt.client as mqtt

from src.config.core import (
    MQTT_HOST,
    MQTT_PORT,
    MQTT_USERNAME,
    MQTT_PASSWORD,
)

from src.mqtt.topics import (
    UPLINK_TOPIC,
)

logging.basicConfig(level=logging.INFO)


class MQTTClient:

    def __init__(self):
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            transport="websockets",
        )

        # NATIVE
        # self.client = mqtt.Client(
        #     mqtt.CallbackAPIVersion.VERSION2,
        # )

        self.client.username_pw_set(
            MQTT_USERNAME,
            MQTT_PASSWORD,
        )

        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message

    def connect(self):
        logging.info(
            f"Connecting to {MQTT_HOST}:{MQTT_PORT}"
        )

        self.client.connect(
            MQTT_HOST,
            MQTT_PORT,
            keepalive=60,
        )

    def start(self):
        self.connect()
        self.client.loop_forever()

    def publish(self, topic, payload):
        if isinstance(payload, dict):
            payload = json.dumps(payload)

        self.client.publish(topic, payload)

    def subscribe(self, topic):
        self.client.subscribe(topic)

    def on_connect(self, client, userdata, flags, reason_code, properties):
        logging.info("MQTT Connected")

        self.subscribe(UPLINK_TOPIC)

    def on_disconnect(self, client, userdata, flags, reason_code, properties):
        logging.warning("MQTT Disconnected")

    def on_message(self, client, userdata, message):
        logging.info(
            f"[{message.topic}] {message.payload.decode()}"
        )