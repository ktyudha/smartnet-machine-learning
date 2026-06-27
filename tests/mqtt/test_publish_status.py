from unittest.mock import MagicMock, patch
from src.mqtt.client import MQTTClient


def make_client() -> MQTTClient:
    with patch("src.mqtt.client.mqtt.Client"):
        c = MQTTClient()
        c.publish = MagicMock()
        return c


def test_publish_status_string():
    c = make_client()
    c.publisher.status("online")
    c.publish.assert_called_once_with("status", "online")


def test_publish_status_dict():
    c = make_client()
    c.publisher.status({"state": "active"})
    c.publish.assert_called_once_with("status", {"state": "active"})


if __name__ == "__main__":
    test_publish_status_string()
    print("PASS: test_publish_status_string")

    test_publish_status_dict()
    print("PASS: test_publish_status_dict")
