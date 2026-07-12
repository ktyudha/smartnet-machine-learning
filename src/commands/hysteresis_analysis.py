import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.config import BASE_DIR, get_logger
from src.commands.generate_dataset import ARCHETYPES, _quality_tier
from src.decision.relay_activation import RelayActivation
from src.inference.predictor import predict

logger = get_logger(__name__)

FIGURES_DIR = BASE_DIR / "reports" / "figures"
REPORTS_DIR = BASE_DIR / "reports"

# noisy_borderline: signal hovering right at a tier boundary with high noise,
# no drift — the exact condition where a naive threshold-follower relay flaps
# on every noisy reading and hysteresis is supposed to earn its keep.
ARCHETYPE = "noisy_borderline"
HYSTERESIS_LEVELS = [1, 2, 3]


def _simulate_session(rng: np.random.Generator, length: int):
    p = ARCHETYPES[ARCHETYPE]
    rssi = rng.uniform(*p["rssi0"])
    snr = rng.uniform(*p["snr0"])
    drift_rssi = rng.uniform(*p["drift"])
    drift_snr = drift_rssi * 0.3
    rssi_noise, snr_noise = p["noise"]

    readings = []
    for _ in range(length):
        rssi += drift_rssi + rng.normal(0, rssi_noise)
        snr += drift_snr + rng.normal(0, snr_noise)
        rssi = float(np.clip(rssi, -145, -20))
        snr = float(np.clip(snr, -20, 16))
        readings.append((round(rssi, 1), round(snr, 1)))
    return readings


def _count_flaps(flags):
    flaps = 0
    prev = False
    for f in flags:
        if f != prev:
            flaps += 1
        prev = f
    return flaps


def _ml_flags(readings, hysteresis):
    relay = RelayActivation(hysteresis=hysteresis)
    flags = []
    for i, (rssi, snr) in enumerate(readings):
        if i < 2:
            flags.append(relay.relay_on)
            continue
        (r2, s2), (r1, s1), (r0, s0) = readings[i - 2:i + 1]
        label = predict(r2, r1, r0, s2, s1, s0)
        flags.append(relay.decide(label))
    return flags


def run(args):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    results = {}
    for hyst in HYSTERESIS_LEVELS:
        flap_counts = []
        for s in range(args.sessions):
            rng = np.random.default_rng(args.seed + s)
            readings = _simulate_session(rng, length=args.session_length)
            flags = _ml_flags(readings, hysteresis=hyst)
            flap_counts.append(_count_flaps(flags))
        results[hyst] = np.array(flap_counts)
        logger.info(
            f"hysteresis={hyst}: avg {results[hyst].mean():.2f} flap/sesi "
            f"(std {results[hyst].std():.2f}), n={args.sessions} sesi noisy_borderline"
        )

    baseline = results[1].mean()
    current = results[2].mean()
    reduction_pct = (1 - current / baseline) * 100 if baseline > 0 else 0.0
    logger.info(
        f"Hysteresis=2 vs tanpa-hysteresis: {reduction_pct:.0f}% lebih sedikit "
        f"perubahan status relay pada kondisi sinyal noisy di sekitar ambang batas"
    )

    _plot_bar_chart(results, reduction_pct)
    _save_table(results)


def _plot_bar_chart(results, reduction_pct):
    labels = [f"Tanpa hysteresis\n(hysteresis=1)" if h == 1 else f"hysteresis={h}" for h in HYSTERESIS_LEVELS]
    means = [results[h].mean() for h in HYSTERESIS_LEVELS]
    stds = [results[h].std() for h in HYSTERESIS_LEVELS]

    fig, ax = plt.subplots(figsize=(7, 5.5))
    colors = ["#e34948" if h == 1 else "#2a78d6" for h in HYSTERESIS_LEVELS]
    bars = ax.bar(labels, means, yerr=stds, capsize=5, color=colors)
    ax.set_ylabel("Rata-rata perubahan status relay per sesi (flap)")
    fig.suptitle("Stabilitas Aktivasi Relay pada Sinyal Noisy di Ambang Batas", fontsize=13, y=0.98)
    ax.set_title(
        f"hysteresis=2 (default sistem) memangkas {reduction_pct:.0f}% perubahan status vs tanpa hysteresis",
        fontsize=9.5, color="#52514e",
    )
    for bar, m in zip(bars, means):
        ax.text(bar.get_x() + bar.get_width() / 2, m + 0.12, f"{m:.2f}", ha="center", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    path = FIGURES_DIR / "hysteresis_stability.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    logger.info(f"Saved {path}")


def _save_table(results):
    import pandas as pd

    rows = [
        {
            "hysteresis": h,
            "avg_flaps_per_session": results[h].mean(),
            "std_flaps_per_session": results[h].std(),
        }
        for h in HYSTERESIS_LEVELS
    ]
    df = pd.DataFrame(rows)
    path = REPORTS_DIR / "hysteresis_stability.csv"
    df.to_csv(path, index=False)
    logger.info(f"Saved {path}")
    print(df.to_string(index=False))
