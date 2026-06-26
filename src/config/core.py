from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

MQTT_USERNAME = os.getenv("MQTT_USERNAME_SERVER")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD_SERVER")

MQTT_HOST = os.getenv("MQTT_BROKER_WS")
MQTT_PORT = int(os.getenv("MQTT_PORT_WS", "1883"))

print("===== ENV =====")
print(f"MQTT_HOST     : {MQTT_HOST}")
print(f"MQTT_PORT     : {MQTT_PORT}")
print(f"MQTT_USERNAME : {MQTT_USERNAME}")
print(f"MQTT_PASSWORD : {'***' if MQTT_PASSWORD else None}")
print("================")