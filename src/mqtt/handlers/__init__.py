from .uplink import handle as uplink_handler
from .downlink import handle as downlink_handler

from src.mqtt.topics import (
    UPLINK_TOPIC,
    DOWNLINK_TOPIC,
)


def get_handlers():
    return {
        UPLINK_TOPIC: uplink_handler,
        DOWNLINK_TOPIC: downlink_handler,
    }