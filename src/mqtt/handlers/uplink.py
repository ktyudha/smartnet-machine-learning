import json

from src.config import get_logger

logger = get_logger(__name__)


def handle(payload: str, mqtt):
    try:
        data = json.loads(payload)

        logger.info("Received uplink")

        #
        # nanti:
        #
        # prediction = predictor.predict(data)
        #
        # mqtt.publish(RELAY_TOPIC, prediction)
        #

    except Exception as e:
        logger.exception(e)