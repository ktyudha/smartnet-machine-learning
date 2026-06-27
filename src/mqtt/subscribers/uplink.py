import json

from src.config import get_logger
from src.mqtt.parser import (
    is_json,
    parse_json,
    parse_plain,
)

logger = get_logger(__name__)


def subscribe(payload: str, mqtt):
    payload = payload.strip()

    if not payload:
        return

    data = (
        parse_json(payload)
        if is_json(payload)
        else parse_plain(payload)
    )

    # TESTING PUBLISH
    mqtt.publisher.status("online")
    
