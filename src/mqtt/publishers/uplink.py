from src.config import get_logger
from src.mqtt.topics import UPLINK_TOPIC

logger = get_logger(__name__)


def publish(payload, mqtt):
    logger.info("[%s] %s", UPLINK_TOPIC, payload)
    mqtt.publish(UPLINK_TOPIC, payload)
