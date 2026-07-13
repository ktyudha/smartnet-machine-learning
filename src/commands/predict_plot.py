from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.config import BASE_DIR, get_logger
from src.commands.generate_dataset import ARCHETYPES, SEVERITY_ORDER, _quality_tier
from src.inference.predictor import predict

logger = get_logger(__name__)

REPORTS_DIR = BASE_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

SEVERITY_COLORS = {
    "Excellent": "#2a9d54",
    "Good": "#8bc34a",
    "Fair": "#f2c14e",
    "Weak": "#f28c28",
    "Poor": "#e34948",
}

# Ordinal score for plotting the categorical label on a single numeric axis —
# Poor=0 .. Excellent=4, reverse of SEVERITY_ORDER (best-to-worst).
QUALITY_SCORE = {label: len(SEVERITY_ORDER) - 1 - i for i, label in enumerate(SEVERITY_ORDER)}


def _load_real_session(path):
    df = pd.read_excel(path) if str(path).endswith(".xlsx") else pd.read_csv(path)

    if "timestamp" in df.columns:
        # raw format is "YYYY:MM:DD HH:MM:SS:mmm" — swap the last ':' (before
        # milliseconds) for '.' so pandas can parse it as a proper timestamp.
        ts = pd.to_datetime(
            df["timestamp"].str.replace(r":(\d{3})$", r".\1", regex=True),
            format="%Y:%m:%d %H:%M:%S.%f",
        )
        df = df.assign(_ts=ts).sort_values("_ts")

    return list(zip(df["rssi"].astype(float), df["snr"].astype(float)))


def _simulate_session(rng: np.random.Generator, archetype: str, length: int):
    p = ARCHETYPES[archetype]
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


def run(args):
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    if args.input:
        input_path = BASE_DIR / args.input if not Path(args.input).is_absolute() else Path(args.input)
        readings = _load_real_session(input_path)
        label = f"data nyata: {input_path.name}"
    else:
        rng = np.random.default_rng(args.seed)
        readings = _simulate_session(rng, args.archetype, args.length)
        label = f"simulasi '{args.archetype}'"

    rows = []
    for i, (rssi, snr) in enumerate(readings):
        row = {
            "t": i, "rssi": rssi, "snr": snr,
            "actual_tier": _quality_tier(rssi, snr),
            "predicted_next": None,
        }
        if i >= 2:
            (r2, s2), (r1, s1), (r0, s0) = readings[i - 2:i + 1]
            row["predicted_next"] = predict(r2, r1, r0, s2, s1, s0)
        rows.append(row)
    df = pd.DataFrame(rows)

    path_csv = REPORTS_DIR / "predict_trend.csv"
    df.to_csv(path_csv, index=False)
    logger.info(f"Saved {path_csv}")
    print(df.to_string(index=False))

    _plot(df, label)
    _plot_projection(df, label)


def _plot(df: pd.DataFrame, session_label: str):
    fig, (ax_rssi, ax_snr) = plt.subplots(2, 1, figsize=(10, 6.5), sharex=True)

    # Band at t+1: predicted_next at row t is the model's forecast for the
    # reading one step ahead, so the shading belongs on the *next* time slot.
    for _, row in df.iterrows():
        quality = row["predicted_next"]
        if pd.isna(quality):
            continue
        t_next = row["t"] + 1
        for ax in (ax_rssi, ax_snr):
            ax.axvspan(t_next - 0.5, t_next + 0.5, color=SEVERITY_COLORS[quality], alpha=0.25, linewidth=0)

    ax_rssi.plot(df["t"], df["rssi"], marker="o", color="#1f3864", linewidth=1.5)
    ax_rssi.set_ylabel("RSSI (dBm)")
    ax_rssi.set_title(f"Tren RSSI/SNR & Prediksi Kualitas Link Berikutnya — {session_label}")

    ax_snr.plot(df["t"], df["snr"], marker="o", color="#7a1f3d", linewidth=1.5)
    ax_snr.set_ylabel("SNR (dB)")
    ax_snr.set_xlabel("Waktu (indeks pembacaan)")

    handles = [plt.Rectangle((0, 0), 1, 1, color=SEVERITY_COLORS[label], alpha=0.25) for label in SEVERITY_ORDER]
    fig.legend(handles, SEVERITY_ORDER, loc="upper center", ncol=5, bbox_to_anchor=(0.5, 1.02), frameon=False)

    fig.tight_layout(rect=(0, 0, 1, 0.94))
    path = FIGURES_DIR / "predict_trend.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    logger.info(f"Saved {path}")


def _plot_projection(df: pd.DataFrame, session_label: str):
    # History: the actual (rule-based) quality tier of every real reading,
    # plotted on a single ordinal axis so it reads like one continuous metric.
    history_t = df["t"].tolist()
    history_score = [QUALITY_SCORE[label] for label in df["actual_tier"]]

    last_t = history_t[-1]
    last_score = history_score[-1]

    # predicted_next on the LAST row is the model's forecast for one reading
    # beyond the data we actually have — i.e. the real one-step-ahead
    # projection, computed from the last 3 real readings.
    ml_label = df["predicted_next"].iloc[-1]
    ml_score = QUALITY_SCORE[ml_label]

    # Naive/reactive baseline: assume the next reading stays at whatever the
    # current one is — no trend, no model, just "next = now".
    naive_label = df["actual_tier"].iloc[-1]
    naive_score = QUALITY_SCORE[naive_label]

    fig, ax = plt.subplots(figsize=(9, 5.5))

    ax.plot(history_t, history_score, marker="o", color="#1f3864", linewidth=1.8, label="Data Aktual (histori)")
    ax.plot(
        [last_t, last_t + 1], [last_score, ml_score],
        linestyle="--", marker="o", color="#2a78d6", linewidth=2, label="Prediksi Model (ML)",
    )
    ax.plot(
        [last_t, last_t + 1], [last_score, naive_score],
        linestyle="--", marker="s", color="#9a9a9a", linewidth=2, label="Prediksi Reaktif (tanpa tren)",
    )

    ax.annotate(
        f"{df['actual_tier'].iloc[-1]}\n(rssi={df['rssi'].iloc[-1]:.0f}, snr={df['snr'].iloc[-1]:.0f})",
        (last_t, last_score), textcoords="offset points", xytext=(0, 12), ha="center", fontsize=8,
    )
    ax.annotate(f"ML: {ml_label}", (last_t + 1, ml_score), textcoords="offset points",
                xytext=(8, 8), ha="left", fontsize=9, color="#2a78d6", fontweight="bold")
    ax.annotate(f"Reaktif: {naive_label}", (last_t + 1, naive_score), textcoords="offset points",
                xytext=(8, -14), ha="left", fontsize=9, color="#6a6a6a", fontweight="bold")

    ax.set_yticks(range(len(SEVERITY_ORDER)))
    ax.set_yticklabels(list(reversed(SEVERITY_ORDER)))
    ax.set_ylim(-0.5, len(SEVERITY_ORDER) - 0.5)
    ax.set_xlabel("Waktu (indeks pembacaan)")
    ax.set_ylabel("Kualitas Link")
    ax.set_title(f"Proyeksi Kualitas Link Berikutnya — {session_label}")
    ax.legend(loc="lower left", fontsize=9, frameon=True)

    fig.tight_layout()
    path = FIGURES_DIR / "predict_projection.png"
    fig.savefig(path, dpi=200)
    plt.close(fig)
    logger.info(f"Saved {path}")
