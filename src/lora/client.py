import csv
import os
import sys
import time
from datetime import datetime

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
    RELAY_ADDRESS,
    RELAY_HYSTERESIS,
    get_logger,
)
from src.decision.node_state import NodeStateRegistry
from src.lora.dto import SensorReading

logger = get_logger(__name__)

PREDICTION_LOG = os.path.join(
    os.path.dirname(__file__), "..", "..", "logs", "predictions.csv"
)
PREDICTION_COLUMNS = [
    "timestamp", "node",
    "rssi_t2", "rssi_t1", "rssi_t0", "snr_t2", "snr_t1", "snr_t0",
    "prediction", "relay_on", "changed",
]


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

        self.link_quality = NodeStateRegistry(hysteresis=RELAY_HYSTERESIS)

    def on_receive(self, from_addr, to_addr, payload, rssi, snr):
        # Flow: log the raw frame -> parse it into a SensorReading -> publish
        # it to MQTT -> feed rssi/snr into that node's trend window -> predict
        # next link quality -> relay ON/OFF decision (with hysteresis) -> on a
        # flip, downlink a command to the relay device and publish the
        # decision to MQTT for monitoring. Anything that doesn't parse is
        # dropped with a warning, never crashes the listener (see
        # LoRaP2P._handle_event).
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

        # Frames forwarded by the relay carry the relay->gateway link's
        # RSSI/SNR, not the node's: feeding them in would mix two links
        # into one trend window and make the relay toggle itself.
        if from_addr == RELAY_ADDRESS:
            return

        state = self.link_quality.get(from_addr)
        label, relay_on, changed = state.observe(float(rssi), float(snr))
        if label is not None:
            self._record_prediction(from_addr, state.window, label, relay_on, changed)
        if not changed:
            return

        command = "RELAY_ON" if relay_on else "RELAY_OFF"
        logger.info(
            "Node %s predicted quality=%s → %s (relay address %s)",
            from_addr, label, command, RELAY_ADDRESS,
        )
        self.send(RELAY_ADDRESS, command)
        # Tell the node too, so it knows the relay is now forwarding for it.
        self.send(from_addr, command)
        mqtt.publish_status(
            {
                "node": from_addr,
                "predicted_quality": label,
                "relay": relay_on,
            }
        )

    def _record_prediction(self, node, window, label, relay_on, changed):
        # One line per prediction: the 3-reading window the model saw
        # (t-2, t-1, t0), the predicted next-link quality, the relay state
        # after hysteresis, which node it came from, and when.
        now = datetime.now()
        (r2, s2), (r1, s1), (r0, s0) = window
        logger.info(
            "PREDICT node=%s window=[t-2:(%s,%s) t-1:(%s,%s) t0:(%s,%s)] "
            "-> %s relay=%s%s",
            node, r2, s2, r1, s1, r0, s0, label,
            "ON" if relay_on else "OFF", " (CHANGED)" if changed else "",
        )
        try:
            os.makedirs(os.path.dirname(PREDICTION_LOG), exist_ok=True)
            new = not os.path.exists(PREDICTION_LOG)
            with open(PREDICTION_LOG, "a", newline="") as f:
                w = csv.writer(f)
                if new:
                    w.writerow(PREDICTION_COLUMNS)
                w.writerow([
                    now.isoformat(timespec="seconds"), node,
                    r2, r1, r0, s2, s1, s0,
                    label, int(relay_on), int(changed),
                ])
        except OSError:
            logger.exception("Gagal menulis %s", PREDICTION_LOG)

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
