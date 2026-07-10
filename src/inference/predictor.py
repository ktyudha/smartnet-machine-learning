import pandas as pd

from src.config import get_logger
from src.inference.load_model import load

logger = get_logger(__name__)

_model = None
_scaler = None


def _get_model():
    global _model, _scaler
    if _model is None:
        _model, _scaler = load()
    return _model, _scaler


def predict(rssi: float, snr: float):
    model, scaler = _get_model()

    X = scaler.transform(pd.DataFrame([[rssi, snr]], columns=["rssi", "snr"]))
    result = int(model.predict(X)[0])

    label = "Relay" if result == 1 else "Direct"
    logger.info(f"Predict rssi={rssi}, snr={snr} → {result} ({label})")

    return result
