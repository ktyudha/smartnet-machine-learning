from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parents[2]
MODELS_DIR = BASE_DIR / "models"
load_dotenv(BASE_DIR / ".env")

MQTT_USERNAME = os.getenv("MQTT_USERNAME_SERVER")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD_SERVER")

MQTT_HOST = os.getenv("MQTT_BROKER_WS")
MQTT_PORT = int(os.getenv("MQTT_PORT_WS", "1883"))

LORA_SERIAL_PORT = os.getenv("LORA_SERIAL_PORT", "/dev/tty.usbserial-110")
LORA_ADDRESS = int(os.getenv("LORA_ADDRESS", "1"))
LORA_FREQUENCY = int(os.getenv("LORA_FREQUENCY", "915000000"))
LORA_SPREADING_FACTOR = int(os.getenv("LORA_SPREADING_FACTOR", "7"))
LORA_BANDWIDTH = int(os.getenv("LORA_BANDWIDTH", "0"))
LORA_CODING_RATE = int(os.getenv("LORA_CODING_RATE", "0"))
LORA_PREAMBLE = int(os.getenv("LORA_PREAMBLE", "8"))
LORA_TX_POWER = int(os.getenv("LORA_TX_POWER", "22"))
LORA_VERBOSE = os.getenv("LORA_VERBOSE", "false").lower() == "true"

RELAY_ADDRESS = int(os.getenv("RELAY_ADDRESS", "2"))
RELAY_HYSTERESIS = int(os.getenv("RELAY_HYSTERESIS", "2"))