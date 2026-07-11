# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

SmartNet ML: a LoRa P2P ↔ MQTT gateway plus the ML pipeline that decides whether a sensor
node should transmit **Direct** or via **Relay**, based on signal quality (RSSI/SNR). Two
independent entry points share the same `src/` codebase:

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
make predict RSSI=-100 SNR=-15   # cli.py predict --rssi --snr
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
- **Downlink**: MQTT subscribes to `v1/devices/downlink-p2p`; `src/mqtt/subscribers/downlink.py`
  currently only parses the payload (JSON or plain) and stops there — it is a stub, not yet wired
  to send anything back over LoRa (`src.lora.send`). `src/decision/relay_activation.py` and
  `src/database/repository.py` are empty placeholder files — the relay-activation decision logic
  and any persistence layer are not implemented yet.
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

### ML pipeline (`src/preprocessing` → `src/training` → `src/inference`)
Binary classification: features `rssi`, `snr` → target `relay` (0=Direct, 1=Relay), model is a
`DecisionTreeClassifier` (`src/algorithms/decision_tree.py`, `random_state=42`).

- `src/preprocessing`: `dataset.py` owns all the fixed data paths (`data/raw/dataset_rssi_snr.csv` →
  `data/interim/dataset_cleaned.csv` → `data/processed/{train,test}.csv`); `cleaning.py` drops
  dupes/NaNs; `scaling.py` does the train/test split (stratified, `test_size=0.2`, `random_state=42`)
  and fits `StandardScaler` **on the train split only**, applying it to test — never re-fit the
  scaler on test data.
- `src/training`: `train.py` fits on the already-scaled train split; `tuning.py` runs `GridSearchCV`
  with `StratifiedKFold` scored on `f1_macro` (class imbalance-aware) over a fixed `PARAM_GRID`;
  `evaluate.py` returns accuracy/classification report/confusion matrix; `save_model.py` persists
  model and scaler as `models/decision_tree.pkl` / `models/scaler.pkl` via `joblib`.
- `src/inference`: `load_model.py` loads both pickles from `MODELS_DIR`; `predictor.py` caches them
  in module-level globals on first call and is what both `cli.py predict` and (eventually) the
  relay-activation decision logic should call.
- `src/training/load_dataset.py` (bare `load_dataset(path)`) is dead/unused — `src/preprocessing/dataset.py:load()`
  is the one actually wired into `prepare`.
- `notebooks/01_exploration.ipynb` → `02_preprocessing.ipynb` → `03_training.ipynb` mirror these
  pipeline stages for interactive/exploratory work; they are not part of the CLI pipeline.

### Logging
`setup_logger()` (called once at the top of both `main.py` and `cli.py`) configures root logging;
every module gets its own logger via `get_logger(__name__)`. Don't call `setup_logger` elsewhere.
