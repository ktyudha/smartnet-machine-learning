from src.config import get_logger

logger = get_logger(__name__)

RELAY_ON_LABELS = {"Weak", "Poor"}


class RelayActivation:
    """Maps predicted link-quality labels to a relay ON/OFF decision.

    The Decision Tree only predicts quality (Excellent/Good/Fair/Weak/Poor); it
    never touches the relay. This class holds that separate business-logic step,
    requiring `hysteresis` consecutive predictions in the new direction before
    flipping state, so a single noisy prediction can't flap the relay.
    """

    def __init__(self, hysteresis: int = 2):
        self.hysteresis = hysteresis
        self._relay_on = False
        self._streak_label = None
        self._streak_count = 0

    @property
    def relay_on(self) -> bool:
        return self._relay_on

    def decide(self, predicted_label: str) -> bool:
        wants_on = predicted_label in RELAY_ON_LABELS

        if wants_on == self._relay_on:
            self._streak_label = None
            self._streak_count = 0
            return self._relay_on

        if predicted_label == self._streak_label:
            self._streak_count += 1
        else:
            self._streak_label = predicted_label
            self._streak_count = 1

        if self._streak_count >= self.hysteresis:
            logger.info(
                "Relay %s after %d consecutive '%s' predictions",
                "ON" if wants_on else "OFF", self._streak_count, predicted_label,
            )
            self._relay_on = wants_on
            self._streak_label = None
            self._streak_count = 0

        return self._relay_on
