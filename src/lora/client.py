import os
import sys
import time

sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "rak3172-at-lib", "protocols"),
)
from lorap2p import LoRaP2P  # noqa: E402

from src import mqtt
from src.config import (
    LORA_SERIAL_PORT,
    LORA_ADDRESS,
    LORA_FREQUENCY,
    LORA_SPREADING_FACTOR,
    LORA_BANDWIDTH,
    LORA_CODING_RATE,
    LORA_PREAMBLE,
    LORA_TX_POWER,
    LORA_VERBOSE,
    get_logger,
)
from src.lora.dto import SensorReading

logger = get_logger(__name__)


class LoRaClient:
    def __init__(self):
        logger.info(
            "Connecting LoRa P2P on %s (addr=%s, freq=%s)",
            LORA_SERIAL_PORT,
            LORA_ADDRESS,
            LORA_FREQUENCY,
        )

        self.device = LoRaP2P(
            serial_port=LORA_SERIAL_PORT,
            address=LORA_ADDRESS,
            frequency=LORA_FREQUENCY,
            spreading_factor=LORA_SPREADING_FACTOR,
            bandwidth=LORA_BANDWIDTH,
            coding_rate=LORA_CODING_RATE,
            preamble=LORA_PREAMBLE,
            tx_power=LORA_TX_POWER,
            on_receive=self.on_receive,
            verbose=LORA_VERBOSE,
        )

    def on_receive(self, from_addr, to_addr, payload, rssi, snr):
        # Flow: log the raw frame -> parse it into a SensorReading -> publish
        # it to MQTT. Anything that doesn't parse is dropped with a warning,
        # never crashes the listener (see LoRaP2P._handle_event).
        logger.info(
            "[%s -> %s] rssi=%s snr=%s payload=%r",
            from_addr,
            to_addr,
            rssi,
            snr,
            payload,
        )

        reading = SensorReading.from_payload(payload)
        if reading is None:
            logger.warning("Payload tidak lengkap: %r", payload)
            return

        mqtt.publish_uplink(
            {
                "metadata": {"rssi": rssi, "snr": snr},
                "uplink": reading.to_dict(),
                "address": {"from": from_addr, "to": to_addr},
                "timestamp": int(time.time() * 1000),
            }
        )

    def start(self):
        logger.info("LoRa P2P ready")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def send(self, to_addr, payload):
        return self.device.send(to_addr, payload)

    def stop(self):
        logger.info("Stopping LoRa P2P")
        self.device.close()
