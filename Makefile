VENV := .venv

ifeq ($(OS),Windows_NT)
    PYTHON := python
    BIN := $(VENV)/Scripts
else
    PYTHON := python3
    BIN := $(VENV)/bin
endif

PYTHON_VENV := $(BIN)/python

.PHONY: help
help:
	@echo "Available commands:"
	@echo "  make install   Create virtualenv & install dependencies"
	@echo "  make run       Run application"
	@echo "  make run-bg    Run application in background (nohup, survives SSH disconnect)"
	@echo "  make stop      Stop background process started with make run-bg"
	@echo "  make logs      Tail logs from run-bg (run.log)"
	@echo "  make freeze    Update requirements.txt"
	@echo "  make clean     Remove virtual environment"
	@echo ""
	@echo "ML Pipeline:"
	@echo "  make prepare   Clean raw data → interim & processed"
	@echo "  make train     Train Decision Tree model"
	@echo "  make evaluate  Evaluate model on full dataset"
	@echo "  make pipeline  Run prepare → train → evaluate"
	@echo "  make tune          GridSearchCV tuning → save best model → evaluate on test set"
	@echo "  make pipeline-tune Run prepare → tune (full pipeline dengan tuning)"
	@echo "  make predict       Contoh: make predict RSSI_T2=-90 RSSI_T1=-95 RSSI_T0=-100 SNR_T2=2 SNR_T1=-2 SNR_T0=-6"
	@echo "  make report        Generate confusion matrix, feature importance, tree diagram -> reports/"
	@echo "  make tune-report   Re-run GridSearchCV, save param search-space + sensitivity evidence -> reports/"
	@echo "  make hysteresis-analysis   Simulate noisy sessions -> relay flap-count comparison -> reports/"
	@echo "  make predict-plot  Contoh: make predict-plot ARCHETYPE=degrading LENGTH=20 SEED=7 -> reports/figures/predict_trend.png"

.PHONY: install
install:
	$(PYTHON) -m venv $(VENV)
	$(PYTHON_VENV) -m ensurepip --upgrade
	$(PYTHON_VENV) -m pip install --upgrade pip
	$(PYTHON_VENV) -m pip install -r requirements.txt

.PHONY: run
run:
	$(PYTHON_VENV) main.py

.PHONY: run-bg
run-bg:
	nohup $(PYTHON_VENV) main.py > run.log 2>&1 & echo $$! > run.pid
	@echo "Started in background (PID $$(cat run.pid)). Logs: run.log. SSH can be closed safely."

.PHONY: stop
stop:
	@if [ -f run.pid ]; then \
		kill $$(cat run.pid) && rm run.pid && echo "Stopped."; \
	else \
		echo "run.pid not found, process may not be running."; \
	fi

.PHONY: logs
logs:
	tail -f run.log

.PHONY: freeze
freeze:
	$(PYTHON_VENV) -m pip freeze > requirements.txt

.PHONY: clean
clean:
	$(PYTHON) -c "import shutil; shutil.rmtree('$(VENV)', ignore_errors=True)"

.PHONY: prepare
prepare:
	$(PYTHON_VENV) cli.py prepare

.PHONY: train
train:
	$(PYTHON_VENV) cli.py train

.PHONY: evaluate
evaluate:
	$(PYTHON_VENV) cli.py evaluate

.PHONY: pipeline
pipeline: prepare train evaluate

.PHONY: tune
tune:
	$(PYTHON_VENV) cli.py tune

.PHONY: pipeline-tune
pipeline-tune: prepare tune

RSSI_T2 ?= -90
RSSI_T1 ?= -95
RSSI_T0 ?= -100
SNR_T2  ?= 2
SNR_T1  ?= -2
SNR_T0  ?= -6

.PHONY: predict
predict:
	$(PYTHON_VENV) cli.py predict \
		--rssi-t2 $(RSSI_T2) --rssi-t1 $(RSSI_T1) --rssi-t0 $(RSSI_T0) \
		--snr-t2 $(SNR_T2) --snr-t1 $(SNR_T1) --snr-t0 $(SNR_T0)

.PHONY: report
report:
	$(PYTHON_VENV) cli.py report

.PHONY: hysteresis-analysis
hysteresis-analysis:
	$(PYTHON_VENV) cli.py hysteresis-analysis

.PHONY: tune-report
tune-report:
	$(PYTHON_VENV) cli.py tune-report

ARCHETYPE ?= degrading
LENGTH    ?= 20
SEED      ?= 7

.PHONY: predict-plot
predict-plot:
	$(PYTHON_VENV) cli.py predict-plot --archetype $(ARCHETYPE) --length $(LENGTH) --seed $(SEED)
# Simulasi node -> gateway -> prediksi -> relay (tanpa hardware).
# Contoh: make simulate SCENARIO=noisy NODES=2 STEPS=50 DELAY=0.1
SCENARIO ?= degrading
NODES ?= 1
STEPS ?= 40
DELAY ?= 0.3

.PHONY: simulate
simulate:
	$(PYTHON_VENV) -m simulation.simulate_gateway --scenario $(SCENARIO) --nodes $(NODES) --steps $(STEPS) --delay $(DELAY)
