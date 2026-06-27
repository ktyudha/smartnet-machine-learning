import json

from src.config import get_logger

logger = get_logger(__name__)


def is_json(payload: str) -> bool:
    try:
        json.loads(payload)
        return True
    except json.JSONDecodeError:
        return False


def parse_json(payload: str):
    return json.loads(payload)


def parse_plain(payload: str):
    return payload.strip()