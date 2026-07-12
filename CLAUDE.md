# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

SmartNet ML: a LoRa P2P ↔ MQTT gateway plus an ML pipeline that predicts the *next* link-quality
state (Excellent/Good/Fair/Weak/Poor) from a short trend window of RSSI/SNR readings, so a
gateway-side business-logic layer can switch a **Relay** on *before* the link actually degrades,
rather than reacting to a threshold breach after the fact. Two independent entry points share the
same `src/` codebase:

- `main.py` — the runtime gateway service (LoRa P2P listener + MQTT bridge, run continuously).
- `cli.py` — the offline ML pipeline CLI (prepare data, train/tune/evaluate the model, predict).

## Commands

Windows uses `python`/`.venv/Scripts`; the Makefile auto-detects OS but Makefile targets
require a `make`-capable shell (e.g. Git Bash) to run on Windows.

```
make install         # create .venv and install requirements.txt
make run             # python main.py — starts the LoRa/MQTT gateway
make run-bg / stop / logs   # background run via nohup (POSIX only), logs to run.log

make prepare         # cli.py prepare  — raw csv -> clean -> train/test split -> scaled + scaler saved
make train           # cli.py train    — fit DecisionTreeClassifier on train split, save model
make tune            # cli.py tune     — GridSearchCV over train split, evaluate on test split, save best model
make evaluate        # cli.py evaluate — evaluate saved model on test split
make pipeline        # prepare -> train -> evaluate
make pipeline-tune   # prepare -> tune
make predict RSSI_T2=-90 RSSI_T1=-95 RSSI_T0=-100 SNR_T2=2 SNR_T1=-2 SNR_T0=-6
```

Other `cli.py` subcommands not wired into the Makefile:
- `python cli.py convert --input <xlsx> --output <csv>` — Excel → CSV for raw data prep.
- `python cli.py lora-ports` — list serial ports and flag which one matches `.env`'s `LORA_SERIAL_PORT`.

There is no test runner configured (no pytest in `requirements.txt`, no pytest config). Tests
are plain scripts with a `if __name__ == "__main__"` block; run them as modules from the repo
root so `src` resolves as a package:

```
python -m tests.mqtt.test_publish_status
```

## Architecture

### Config (`src/config`)
`core.py` loads `.env` from the repo root once and exposes every MQTT/LoRa setting as a module
constant (`MQTT_HOST`, `LORA_SERIAL_PORT`, etc.) plus `MODELS_DIR`. `src/config/__init__.py`
re-exports these alongside `setup_logger`/`get_logger`. This is the only place env vars are
read — everything else imports from `src.config`.

### Gateway data flow (`main.py`)
`main.py` starts MQTT on a background thread and runs the LoRa listener on the main thread;
`mqtt.stop()` runs in a `finally` so a Ctrl-C on the LoRa side still closes MQTT cleanly.

- **Uplink**: `LoRaP2P` (vendored library, see below) receives a framed packet → `LoRaClient.on_receive`
  parses the payload into a `SensorReading` DTO (`src/lora/dto/sensor_reading.py`, semicolon-delimited
  `temperature;humidity;ph;nitrogen;phosphorus;potassium`) → published to MQTT on `v1/devices/uplink-p2p`
  with rssi/snr metadata attached. Malformed payloads are dropped with a warning, never raised.
- **Predictive relay activation**: a single uplink only carries the *current* RSSI/SNR, but the
  model needs a 3-reading trend window — so `LoRaClient` keeps a `NodeStateRegistry`
  (`src/decision/node_state.py`), one `NodeState` per node address, created lazily on first
  sighting. Every `on_receive` feeds `(rssi, snr)` into that node's `NodeState.observe()`, which
  buffers into a `deque(maxlen=3)`; the first two readings from a node return `(None, None,
  False)` since there isn't a full window yet. Once full, it calls `predictor.predict()` and the
  node's own `RelayActivation.decide()` (hysteresis is per-node, not global — one busy node's
  flapping link can't affect another node's relay state). `on_receive` only acts on a `changed`
  edge: it downlinks a `"RELAY_ON"`/`"RELAY_OFF"` command via `self.send(RELAY_ADDRESS, ...)`
  (env-configured node address, not the MQTT downlink path) and publishes the decision to MQTT
  `status` for monitoring. Exceptions here are caught by `LoRaP2P._handle_event`'s outer try/except
  same as the rest of `on_receive` — never crashes the RX thread.
- **Downlink (MQTT→LoRa)**: MQTT subscribes to `v1/devices/downlink-p2p`;
  `src/mqtt/subscribers/downlink.py` currently only parses the payload (JSON or plain) and stops
  there — a stub, unrelated to the relay-activation path above (this is for the server pushing
  commands *to a node*, not the gateway deciding on the relay).
  `src/database/repository.py` is an empty placeholder — no persistence layer implemented yet.
  `NodeStateRegistry` state is in-memory only and resets on gateway restart.
- Both `src/lora/__init__.py` and `src/mqtt/__init__.py` follow the same pattern: a lazily-created
  module-level singleton client (`client()`) with `start`/`stop`/`send`-or-`publish` wrapper functions,
  so callers never touch `LoRaClient`/`MQTTClient` directly.

### MQTT structure (`src/mqtt`)
Topics are centralized in `topics.py`. `Subscriber` (`subscriber.py`) is a topic → handler-function
map (currently only `DOWNLINK_TOPIC`); `Publisher` (`publisher.py`) exposes one method per outbound
message type, delegating to `src/mqtt/publishers/*.py`. To add a new inbound/outbound message type,
add a topic constant, a handler/publisher module under `publishers/`/`subscribers/`, and register it
in `Publisher`/`Subscriber` — don't grow `client.py` itself.

### Vendored LoRa library (`src/lora/rak3172-at-lib`)
`lib/rak3172.py` (AT-command driver for the RAK3172 module) and `protocols/lorap2p.py` (addressed
P2P framing: `[from_addr:1][to_addr:1][payload:N]`, retry-on-send, auto re-arm RX after each receive)
are a self-contained vendored library, imported via `sys.path.insert` in both `lorap2p.py` and
`src/lora/client.py` rather than as a normal package — keep that in mind when navigating imports
under `src/lora`. `lorap2p.py` documents an extension point (`encoders`/`decoders` lists) for a future
payload security layer (encryption/HMAC) without touching framing/retry logic.

### ML pipeline (`src/preprocessing` → `src/training` → `src/inference` → `src/decision`)
Multi-class classification, not binary: features are a 3-reading RSSI/SNR trend window
(`rssi_t2, rssi_t1, rssi_t0, snr_t2, snr_t1, snr_t0, delta_rssi_1, delta_rssi_2, delta_snr_1,
delta_snr_2` — `t2` oldest, `t0` most recent, `delta_X_1 = X(t1)-X(t2)`, `delta_X_2 = X(t0)-X(t1)`,
see `src/preprocessing/scaling.py:FEATURES`), target is `label` with 5 classes (`Excellent`,
`Good`, `Fair`, `Weak`, `Poor`). Model is a `DecisionTreeClassifier`
(`src/algorithms/decision_tree.py`, `random_state=42`). **The model never touches the relay** —
it only predicts a quality class; a separate business-logic layer decides ON/OFF (see below). The
raw dataset also carries a `relay` column (0/1) purely as a convenience label — it's `1` iff
`label` is `Weak`/`Poor` — but it is *not* a training feature or target; using it as a feature
would leak the target.

- `src/preprocessing`: `dataset.py` owns all the fixed data paths (`data/raw/dataset_rssi_snr.csv` →
  `data/interim/dataset_cleaned.csv` → `data/processed/{train,test}.csv`); `cleaning.py` drops
  dupes/NaNs; `scaling.py` does the train/test split (stratified on the 5-class `label`,
  `test_size=0.2`, `random_state=42`) and fits `StandardScaler` **on the train split only**,
  applying it to test — never re-fit the scaler on test data. `save_splits` writes the target
  column back out under whatever name `TARGET` is (currently `label`), not a hardcoded name.
- `src/training`: `train.py` fits on the already-scaled train split; `tuning.py` runs `GridSearchCV`
  with `StratifiedKFold` scored on `f1_macro` (multi-class-imbalance-aware) over a fixed
  `PARAM_GRID`; `evaluate.py` returns accuracy/classification report/confusion matrix (class names
  come from the data, not hardcoded); `save_model.py` persists model and scaler as
  `models/decision_tree.pkl` / `models/scaler.pkl` via `joblib`.
- `src/inference/predictor.py`: `predict(rssi_t2, rssi_t1, rssi_t0, snr_t2, snr_t1, snr_t0)` builds
  the same 10 features (computing the two deltas itself) and returns the predicted quality label
  as a string. `load_model.py` loads both pickles from `MODELS_DIR`; `predictor.py` caches them in
  module-level globals on first call.
- `src/decision/relay_activation.py`: `RelayActivation` is the business-logic layer the mentor
  discussion asked for — it maps a predicted label to ON/OFF via `RELAY_ON_LABELS = {"Weak",
  "Poor"}`, but only flips state after `hysteresis` (default 2, env `RELAY_HYSTERESIS`)
  *consecutive* predictions agree on the new direction, so a single noisy prediction can't flap the
  relay. `src/decision/node_state.py` wraps one `RelayActivation` + one 3-reading window per node
  and is what the live gateway actually uses (see the predictive-relay-activation bullet under
  gateway data flow above). `cli.py predict` calls `predictor.predict()` once and shows the
  immediate no-hysteresis mapping for a quick sanity check — that CLI path does not go through
  `NodeState`/`RelayActivation` at all, since a single-shot CLI call has no session to hold
  hysteresis state across calls.
- `src/training/load_dataset.py` (bare `load_dataset(path)`) is dead/unused — `src/preprocessing/dataset.py:load()`
  is the one actually wired into `prepare`.
- `notebooks/01_exploration.ipynb` → `02_preprocessing.ipynb` → `03_training.ipynb` mirror these
  pipeline stages for interactive/exploratory work; they predate the multi-class/trend-feature
  rework and have not been updated to match — treat them as stale until revisited.

**On labeling** (per the research discussion this pipeline implements): the target should ideally
represent the *next* window's quality, not the current window's — otherwise the model just
re-learns a threshold rule instead of a genuine degradation trend. Whatever generates
`data/raw/dataset_rssi_snr.csv` is responsible for that shift; nothing in this pipeline enforces
it, so check the label semantics in your dataset before trusting the "predictive" framing.

### Logging
`setup_logger()` (called once at the top of both `main.py` and `cli.py`) configures root logging;
every module gets its own logger via `get_logger(__name__)`. Don't call `setup_logger` elsewhere.
