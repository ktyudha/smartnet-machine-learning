import pandas as pd

from src.config import get_logger
from src.inference.load_model import load
from src.preprocessing.scaling import FEATURES

logger = get_logger(__name__)

_model = None
_scaler = None


def _get_model():
    global _model, _scaler
    if _model is None:
        _model, _scaler = load()
    return _model, _scaler


def predict(rssi_t2: float, rssi_t1: float, rssi_t0: float,
            snr_t2: float, snr_t1: float, snr_t0: float) -> str:
    """Predict the next link-quality class from a 3-reading RSSI/SNR trend window.

    t2 is the oldest reading, t0 the most recent — matching the training features.
    """
    model, scaler = _get_model()

    row = {
        "rssi_t2": rssi_t2, "rssi_t1": rssi_t1, "rssi_t0": rssi_t0,
        "snr_t2": snr_t2, "snr_t1": snr_t1, "snr_t0": snr_t0,
        "delta_rssi_1": rssi_t1 - rssi_t2,
        "delta_rssi_2": rssi_t0 - rssi_t1,
        "delta_snr_1": snr_t1 - snr_t2,
        "delta_snr_2": snr_t0 - snr_t1,
    }

    X = pd.DataFrame(
        scaler.transform(pd.DataFrame([row])[FEATURES]), columns=FEATURES
    )
    label = str(model.predict(X)[0])

    logger.info(
        "Predict rssi=[%s,%s,%s] snr=[%s,%s,%s] → %s",
        rssi_t2, rssi_t1, rssi_t0, snr_t2, snr_t1, snr_t0, label,
    )

    return label
