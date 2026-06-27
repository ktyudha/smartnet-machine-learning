import json

import paho.mqtt.client as mqtt


from src.config import (
    MQTT_HOST,
    MQTT_PASSWORD,
    MQTT_PORT,
    MQTT_USERNAME,

    get_logger
)

from src.mqtt.subscriber import Subscriber
from src.mqtt.publisher import Publisher

logger = get_logger(__name__)


class MQTTClient:

    def __init__(self):
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            transport="websockets",
        )

        self.client.username_pw_set(
            MQTT_USERNAME,
            MQTT_PASSWORD,
        )

        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message

        self.subscriber = Subscriber(self)
        self.publisher = Publisher(self)

    def connect(self):
        logger.info(
            "Connecting MQTT %s:%s",
            MQTT_HOST,
            MQTT_PORT,
        )

        self.client.connect(
            MQTT_HOST,
            MQTT_PORT,
            keepalive=60,
        )

    def start(self):
        self.connect()

        try:
            logger.info("Starting MQTT loop")
            self.client.loop_forever()
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        logger.info("Stopping MQTT")
        self.client.disconnect()

    def publish(self, topic: str, payload):
        if isinstance(payload, dict):
            payload = json.dumps(payload)

        result = self.client.publish(topic, payload)

        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            logger.error("Failed publish to %s", topic)

    def subscribe(self, topic: str):
        logger.info("Subscribe %s", topic)
        self.client.subscribe(topic)

    def on_connect(
        self,
        client,
        userdata,
        flags,
        reason_code,
        properties,
    ):
        logger.info("Connected")

        for topic in self.subscriber.topics():
            self.subscribe(topic)

    def on_disconnect(
        self,
        client,
        userdata,
        flags,
        reason_code,
        properties,
    ):
        logger.warning("Disconnected")

    def on_message(
        self,
        client,
        userdata,
        message,
    ):
        payload = message.payload.decode()

        logger.info(
            "[%s] %s",
            message.topic,
            payload,
        )

        self.subscriber.dispatch(message.topic, payload)