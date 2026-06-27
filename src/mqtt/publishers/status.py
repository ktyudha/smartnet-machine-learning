from src.config import get_logger
from src.mqtt.topics import STATUS_TOPIC

logger = get_logger(__name__)


def publish(payload: str, mqtt):
    logger.info("[%s] %s", STATUS_TOPIC, payload)
    mqtt.publish(STATUS_TOPIC, payload)
