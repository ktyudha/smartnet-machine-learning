from src.config import get_logger

logger = get_logger(__name__)


def handle(payload: str, mqtt):
    logger.info("Relay response: %s", payload)