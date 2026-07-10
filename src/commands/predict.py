from src.config import get_logger
from src.inference.predictor import predict

logger = get_logger(__name__)


def run(args):
    result = predict(float(args.rssi), float(args.snr))
    label = "Relay" if result == 1 else "Direct"
    print(f"Prediction: {result} ({label})")
