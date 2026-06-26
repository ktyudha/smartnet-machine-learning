from src.mqtt.client import MQTTClient

def main():
    mqtt = MQTTClient()
    mqtt.start()

if __name__ == "__main__":
    main()