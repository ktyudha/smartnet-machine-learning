from serial.tools import list_ports

from src.config import LORA_SERIAL_PORT, get_logger

logger = get_logger(__name__)


def _same_port(device: str, configured: str) -> bool:
    # macOS registers each USB-serial adapter under two paths for the same
    # physical port (/dev/tty.* and /dev/cu.*), so compare by suffix.
    return device.rsplit(".", 1)[-1] == configured.rsplit(".", 1)[-1]


def run(args):
    ports = list(list_ports.comports())

    if not ports:
        print("Tidak ada serial port terdeteksi.")
        return

    print(f"LORA_SERIAL_PORT saat ini (.env): {LORA_SERIAL_PORT}\n")
    print("Serial port yang tersedia:")
    for port in ports:
        marker = "  <-- ini" if _same_port(port.device, LORA_SERIAL_PORT) else ""
        print(f"  {port.device:30s} {port.description}{marker}")
