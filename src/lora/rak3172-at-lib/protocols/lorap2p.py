"""Reusable LoRa P2P protocol layer for the RAK3172 module.

Wraps addressed send/receive over `AT+PSEND` / `+EVT:RXP2P` so application
code (a relay, a gateway that republishes over MQTT, a node, ...) never has
to touch AT commands or packet framing directly.

Frame layout: [from_addr:1][to_addr:1][payload:N]

Extension point: `encoders`/`decoders` are lists of `bytes -> bytes`
transforms applied to the payload on send/receive, in order. This is where
a future security layer (encryption, HMAC, ...) plugs in without touching
the framing/retry logic below.
"""

import logging
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from rak3172 import RAK3172

logger = logging.getLogger(__name__)


class LoRaP2P:
    def __init__(
        self,
        serial_port,
        address,
        frequency,
        spreading_factor,
        bandwidth,
        coding_rate,
        preamble,
        tx_power,
        on_receive=None,
        encoders=None,
        decoders=None,
        verbose=False,
    ):
        self.address = address
        self.on_receive = on_receive
        self.encoders = encoders or []
        self.decoders = decoders or []

        self.device = RAK3172(
            serial_port=serial_port,
            network_mode=RAK3172.NETWORK_MODES.P2P,
            verbose=verbose,
            callback_events=self._handle_event,
        )
        self.device.configure_p2p(
            frequency=frequency,
            spreading_factor=spreading_factor,
            bandwidth=bandwidth,
            coding_rate=coding_rate,
            preamble=preamble,
            tx_power=tx_power,
        )

    def _handle_event(self, event_type, parameter):
        # Runs on the RX thread: never let a malformed frame or a failing
        # decoder/callback propagate, or the whole listener silently dies.
        if event_type != RAK3172.EVENTS.RECEIVED:
            logger.debug("LoRaP2P - unhandled event %s: %s", event_type, parameter)
            return

        try:
            rssi, snr, hex_payload = parameter.split(":")
            raw = bytes.fromhex(hex_payload)
            from_addr, to_addr, payload = raw[0], raw[1], raw[2:]
        except (ValueError, IndexError) as exc:
            logger.warning("LoRaP2P - dropping malformed frame %r: %s", parameter, exc)
            return

        try:
            for decoder in reversed(self.decoders):
                payload = decoder(payload)
        except Exception as exc:
            logger.warning("LoRaP2P - dropping frame rejected by decoder: %s", exc)
            return

        if self.on_receive:
            try:
                self.on_receive(from_addr, to_addr, payload, rssi, snr)
            except Exception:
                logger.exception("LoRaP2P - on_receive callback raised")

    def send(self, to_addr, payload, retries=3, retry_delay=0.5):
        """Frame `payload` with the from/to address header and transmit it, retrying on failure."""
        if isinstance(payload, str):
            payload = payload.encode("utf-8")

        for encoder in self.encoders:
            payload = encoder(payload)

        frame = bytes([self.address, to_addr]) + payload
        return self._send_raw(frame.hex(), retries=retries, retry_delay=retry_delay)

    def _send_raw(self, hex_payload, retries, retry_delay):
        for attempt in range(1, retries + 1):
            try:
                self.device.send_command(f"AT+PRECV={RAK3172.P2P_RX.DISABLE}")
                time.sleep(0.2)
                if self.device.send_p2p_payload(hex_payload):
                    time.sleep(0.2)
                    self.device.send_command(f"AT+PRECV={RAK3172.P2P_RX.CONTINUOUS}")
                    return True
            except Exception as exc:
                logger.warning("LoRaP2P - send retry %d/%d failed: %s", attempt, retries, exc)
            time.sleep(retry_delay)

        logger.error("LoRaP2P - send failed after %d attempts", retries)
        return False

    def close(self):
        self.device.send_command(f"AT+PRECV={RAK3172.P2P_RX.DISABLE}")
        self.device.close()
