import threading

from src import lora, mqtt
from src.config import setup_logger

def main():
    setup_logger()

    mqtt_thread = threading.Thread(target=mqtt.start, daemon=True)
    mqtt_thread.start()

    try:
        lora.start()
    finally:
        mqtt.stop()


if __name__ == "__main__":
    main()