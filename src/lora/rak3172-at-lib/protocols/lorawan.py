"""Reusable LoRaWAN protocol layer for the RAK3172 module.

Wraps join/uplink/downlink handling behind a small callback-based API so
application code (a node reporting sensor data, a gateway relaying it
elsewhere, ...) never has to touch AT commands or session state directly.

Extension point: `encoders`/`decoders` are lists of `bytes -> bytes`
transforms applied to the payload on send/receive, in order. This is where
a future security layer (encryption, HMAC, ...) plugs in without touching
the join/session logic below.
"""

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))
from rak3172 import RAK3172

logger = logging.getLogger(__name__)


class LoRaWAN:
    class STATE:
        DISCONNECTED = 0
        JOINING = 1
        JOINED = 2

    def __init__(
        self,
        serial_port,
        deveui,
        joineui,
        appkey,
        on_join=None,
        on_confirm=None,
        on_receive=None,
        encoders=None,
        decoders=None,
        verbose=False,
    ):
        self.on_join = on_join
        self.on_confirm = on_confirm
        self.on_receive = on_receive
        self.encoders = encoders or []
        self.decoders = decoders or []
        self.state = LoRaWAN.STATE.DISCONNECTED

        self.device = RAK3172(
            serial_port=serial_port,
            network_mode=RAK3172.NETWORK_MODES.LORAWAN,
            verbose=verbose,
            callback_events=self._handle_event,
        )
        self.device.deveui = deveui
        self.device.joineui = joineui
        self.device.appkey = appkey

    def _handle_event(self, event_type, parameter):
        # Runs on the RX thread: never let a failing callback propagate,
        # or the whole listener silently dies.
        if event_type == RAK3172.EVENTS.JOINED:
            self.state = LoRaWAN.STATE.JOINED
            if self.on_join:
                try:
                    self.on_join()
                except Exception:
                    logger.exception("LoRaWAN - on_join callback raised")
        elif event_type == RAK3172.EVENTS.SEND_CONFIRMATION:
            if self.on_confirm:
                try:
                    self.on_confirm(parameter)
                except Exception:
                    logger.exception("LoRaWAN - on_confirm callback raised")
        else:
            logger.debug("LoRaWAN - unhandled event %s: %s", event_type, parameter)

    def join(self):
        self.state = LoRaWAN.STATE.JOINING
        self.device.join()

    def is_joined(self):
        return self.state == LoRaWAN.STATE.JOINED

    def send(self, fport, payload, confirmed=False):
        """Encode `payload` to the hex-ASCII form `AT+SEND` expects and transmit it on `fport`."""
        if isinstance(payload, str):
            payload = payload.encode("utf-8")

        for encoder in self.encoders:
            payload = encoder(payload)

        return self.device.send_payload(fport, payload.hex().encode("ascii"), confirmed=confirmed)

    def receive(self):
        raw = self.device.getdata
        hex_payload = raw.split(":")[-1].strip()
        payload = bytes.fromhex(hex_payload)

        for decoder in reversed(self.decoders):
            payload = decoder(payload)

        if self.on_receive:
            self.on_receive(payload)

        return payload

    def close(self):
        self.device.close()
