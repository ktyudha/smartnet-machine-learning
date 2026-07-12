import numpy as np
import pandas as pd

from src.config import BASE_DIR, get_logger

logger = get_logger(__name__)

SEVERITY_ORDER = ["Excellent", "Good", "Fair", "Weak", "Poor"]

# Expected mean SNR per RSSI-implied base tier — calibrated from the
# descriptive stats of the original (window-based) dataset's mean_rssi /
# mean_snr per label, so the physical RSSI/SNR ranges per tier stay
# consistent with what the thesis already documents. Only *when* the rule
# is applied changes: here it's applied to the next reading (t+1), not the
# window's own mean, so the window has to forecast it rather than describe it.
EXPECTED_SNR = {0: 9.7, 1: 3.1, 2: -0.3, 3: -3.1, 4: -8.5}
RSSI_BASE_CUTS = [-65, -85, -97, -108]  # 4 cuts -> 5 base tiers, best to worst

# Archetypes a simulated node's link can follow across one session: a
# starting RSSI/SNR range, a per-step drift range (0 for stable), and
# per-step noise std — a slow drift (trend) plus fast noise (fading), same
# structure as a real fading channel with a moving baseline.
ARCHETYPES = {
    "stable_good":      dict(rssi0=(-60, -35), snr0=(6, 15), drift=(0.0, 0.0), noise=(2.5, 1.5)),
    "stable_medium":    dict(rssi0=(-90, -70), snr0=(-1, 5), drift=(0.0, 0.0), noise=(2.5, 1.5)),
    "stable_poor":      dict(rssi0=(-135, -100), snr0=(-12, -2), drift=(0.0, 0.0), noise=(3.0, 2.0)),
    "degrading":        dict(rssi0=(-70, -40), snr0=(4, 12), drift=(-4.0, -1.5), noise=(2.5, 1.5)),
    "improving":        dict(rssi0=(-135, -100), snr0=(-10, -1), drift=(1.5, 4.0), noise=(2.5, 1.5)),
    "noisy_borderline": dict(rssi0=(-105, -80), snr0=(-4, 3), drift=(0.0, 0.0), noise=(5.0, 3.0)),
}

TRANSITION_ARCHETYPES = {"degrading", "improving", "noisy_borderline"}


def _quality_tier(rssi: float, snr: float) -> str:
    base = 0
    for cut in RSSI_BASE_CUTS:
        if rssi < cut:
            base += 1

    expected = EXPECTED_SNR[base]
    if snr - expected > 5 and base > 0:
        base -= 1
    elif snr - expected < -5 and base < len(SEVERITY_ORDER) - 1:
        base += 1

    return SEVERITY_ORDER[base]


def _simulate_session(rng: np.random.Generator, length: int):
    archetype = rng.choice(list(ARCHETYPES.keys()))
    p = ARCHETYPES[archetype]

    rssi = rng.uniform(*p["rssi0"])
    snr = rng.uniform(*p["snr0"])
    drift_rssi = rng.uniform(*p["drift"])
    drift_snr = drift_rssi * 0.3  # SNR tends to move with RSSI, on a softer slope
    rssi_noise, snr_noise = p["noise"]

    readings = []
    for _ in range(length):
        rssi += drift_rssi + rng.normal(0, rssi_noise)
        snr += drift_snr + rng.normal(0, snr_noise)
        rssi = float(np.clip(rssi, -145, -20))
        snr = float(np.clip(snr, -20, 16))
        readings.append((round(rssi, 1), round(snr, 1)))

    return archetype, readings


def _windows_from_session(session_id: str, archetype: str, readings: list) -> list:
    source = "synthetic_transition" if archetype in TRANSITION_ARCHETYPES else "synthetic"
    rows = []

    for i in range(len(readings) - 3):
        (r2, s2), (r1, s1), (r0, s0), (rn, sn) = readings[i:i + 4]
        label = _quality_tier(rn, sn)

        rows.append(
            {
                "session_id": session_id,
                "source": source,
                "rssi_t2": r2, "rssi_t1": r1, "rssi_t0": r0,
                "snr_t2": s2, "snr_t1": s1, "snr_t0": s0,
                "delta_rssi_1": round(r1 - r2, 2),
                "delta_rssi_2": round(r0 - r1, 2),
                "delta_snr_1": round(s1 - s2, 2),
                "delta_snr_2": round(s0 - s1, 2),
                "mean_rssi": round((r2 + r1 + r0) / 3, 2),
                "mean_snr": round((s2 + s1 + s0) / 3, 2),
                "label": label,
                "relay": int(label in ("Weak", "Poor")),
            }
        )

    return rows


def run(args):
    rng = np.random.default_rng(args.seed)

    rows = []
    for i in range(args.sessions):
        archetype, readings = _simulate_session(rng, length=args.session_length)
        rows.extend(_windows_from_session(f"sim_{i:05d}", archetype, readings))

    df = pd.DataFrame(rows)
    df.insert(0, "id", range(1, len(df) + 1))

    out_path = BASE_DIR / args.output
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)

    logger.info(f"Generated {len(df)} rows from {args.sessions} sessions -> {out_path}")
    logger.info(f"Label distribution:\n{df['label'].value_counts().reindex(SEVERITY_ORDER)}")
