"""Simulasi node -> gateway -> prediksi -> relay, tanpa hardware LoRa / MQTT.

Pakai NodeStateRegistry + model asli (sama persis dengan LoRaClient.on_receive),
hanya sumber datanya yang dummy.

Jalankan dari root repo:
    python -m simulation.simulate_gateway
    python -m simulation.simulate_gateway --scenario degrading --nodes 2 --steps 40 --delay 0.2
    python -m simulation.simulate_gateway --scenario noisy --seed 7 --delay 0
"""
import argparse
import random
import time

from src.config import RELAY_HYSTERESIS
from src.decision.node_state import NodeStateRegistry

SCENARIOS = {
    # (rssi_awal, snr_awal, drift_rssi/step, drift_snr/step, noise_rssi, noise_snr)
    "stable":    (-60, 10, 0.0, 0.0, 1.5, 0.5),
    "degrading": (-60, 10, -1.6, -0.35, 1.5, 0.5),
    "improving": (-120, -10, 1.6, 0.35, 1.5, 0.5),
    "noisy":     (-100, 0, 0.0, 0.0, 6.0, 2.5),   # hovering di batas Fair/Weak
}


class DummyNode:
    """Node palsu: menghasilkan (rssi, snr) tiap step."""

    def __init__(self, addr, scenario, rng):
        self.addr = addr
        self.rng = rng
        self.rssi, self.snr, self.d_rssi, self.d_snr, self.n_rssi, self.n_snr = SCENARIOS[scenario]

    def read(self):
        rssi = self.rssi + self.rng.gauss(0, self.n_rssi)
        snr = self.snr + self.rng.gauss(0, self.n_snr)
        self.rssi = max(-135, min(-20, self.rssi + self.d_rssi))
        self.snr = max(-20, min(15, self.snr + self.d_snr))
        return round(rssi), round(snr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", choices=SCENARIOS, default="degrading")
    ap.add_argument("--nodes", type=int, default=1)
    ap.add_argument("--steps", type=int, default=40)
    ap.add_argument("--delay", type=float, default=0.3, help="detik antar paket (0 = instan)")
    ap.add_argument("--hysteresis", type=int, default=RELAY_HYSTERESIS)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    registry = NodeStateRegistry(hysteresis=args.hysteresis)
    nodes = [DummyNode(i + 1, args.scenario, rng) for i in range(args.nodes)]

    print(f"scenario={args.scenario} nodes={args.nodes} hysteresis={args.hysteresis}\n")
    print(f"{'step':>4} {'node':>4} {'rssi':>5} {'snr':>4}  {'prediksi':<10} relay")
    flaps = {n.addr: 0 for n in nodes}

    for step in range(1, args.steps + 1):
        for node in nodes:
            rssi, snr = node.read()
            label, relay_on, changed = registry.get(node.addr).observe(rssi, snr)
            if label is None:
                print(f"{step:>4} {node.addr:>4} {rssi:>5} {snr:>4}  (mengisi window)")
            else:
                note = ""
                if changed:
                    flaps[node.addr] += 1
                    note = f"  <-- RELAY_{'ON' if relay_on else 'OFF'} dikirim ke downlink"
                print(f"{step:>4} {node.addr:>4} {rssi:>5} {snr:>4}  {label:<10} {'ON' if relay_on else 'off'}{note}")
        if args.delay:
            time.sleep(args.delay)

    print("\nJumlah perubahan relay per node:", flaps)


if __name__ == "__main__":
    main()
