from collections import deque

from src.decision.relay_activation import RelayActivation
from src.inference.predictor import predict

WINDOW_SIZE = 3


class NodeState:
    """One node's rolling RSSI/SNR window plus its relay decision state.

    A single uplink only carries the current RSSI/SNR — the model needs a
    3-reading trend window, so each node's last 3 readings are buffered here
    across calls until there's enough history to predict from.
    """

    def __init__(self, hysteresis: int):
        self._history = deque(maxlen=WINDOW_SIZE)
        self.relay = RelayActivation(hysteresis=hysteresis)

    @property
    def window(self):
        """The buffered readings, oldest (t-2) first, as [(rssi, snr), ...]."""
        return list(self._history)

    def observe(self, rssi: float, snr: float):
        """Feed one new reading.

        Returns (label, relay_on, changed). While the window is still filling
        (first two readings from a node), label and relay_on are None.
        """
        self._history.append((rssi, snr))
        if len(self._history) < WINDOW_SIZE:
            return None, None, False

        (rssi_t2, snr_t2), (rssi_t1, snr_t1), (rssi_t0, snr_t0) = self._history

        label = predict(rssi_t2, rssi_t1, rssi_t0, snr_t2, snr_t1, snr_t0)

        was_on = self.relay.relay_on
        relay_on = self.relay.decide(label)

        return label, relay_on, relay_on != was_on


class NodeStateRegistry:
    """One NodeState per LoRa node address, created lazily on first sighting."""

    def __init__(self, hysteresis: int = 2):
        self.hysteresis = hysteresis
        self._nodes = {}

    def get(self, node_addr) -> NodeState:
        if node_addr not in self._nodes:
            self._nodes[node_addr] = NodeState(hysteresis=self.hysteresis)
        return self._nodes[node_addr]
