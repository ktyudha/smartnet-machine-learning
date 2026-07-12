from src.config import get_logger
from src.decision.relay_activation import RELAY_ON_LABELS
from src.inference.predictor import predict

logger = get_logger(__name__)


def run(args):
    label = predict(
        float(args.rssi_t2), float(args.rssi_t1), float(args.rssi_t0),
        float(args.snr_t2), float(args.snr_t1), float(args.snr_t0),
    )
    relay_suggested = label in RELAY_ON_LABELS

    print(f"Predicted next link quality: {label}")
    print(f"Relay suggested (no hysteresis, single-shot): {relay_suggested}")
