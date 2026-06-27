from src import mqtt
from src.config import setup_logger

def main():
    setup_logger()
    mqtt.start()
    

if __name__ == "__main__":
    main()