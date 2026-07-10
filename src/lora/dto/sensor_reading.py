"""Data shape for the LoRa P2P sensor uplink frame.

Frame layout (payload as ASCII text, semicolon-separated):
    temperature;humidity;ph;nitrogen;phosphorus;potassium

Example: b"7.30;100;4.6;152;15;274"
"""

from dataclasses import asdict, dataclass
from typing import Optional

FIELD_COUNT = 6


@dataclass(frozen=True)
class SensorReading:
    temperature: float
    humidity: float
    ph: float
    nitrogen: int
    phosphorus: int
    potassium: int

    @classmethod
    def from_payload(cls, payload: bytes) -> Optional["SensorReading"]:
        """Parse a raw LoRa payload. Returns None if the frame doesn't match."""
        parts = payload.decode("utf-8", errors="ignore").strip().split(";")
        if len(parts) < FIELD_COUNT:
            return None

        try:
            return cls(
                temperature=float(parts[0]),
                humidity=float(parts[1]),
                ph=float(parts[2]),
                nitrogen=int(parts[3]),
                phosphorus=int(parts[4]),
                potassium=int(parts[5]),
            )
        except ValueError:
            return None

    def to_dict(self, index: int = 1) -> dict:
        return {"index": index, **asdict(self)}
