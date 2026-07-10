VENV := .venv

ifeq ($(OS),Windows_NT)
    PYTHON := python
    BIN := $(VENV)/Scripts
else
    PYTHON := python3.12
    BIN := $(VENV)/bin
endif

PYTHON_VENV := $(BIN)/python

.PHONY: help
help:
	@echo "Available commands:"
	@echo "  make install   Create virtualenv & install dependencies"
	@echo "  make run       Run application"
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
	@echo "  make predict       Contoh: make predict RSSI=-112 SNR=-18.5"

.PHONY: install
install:
	$(PYTHON) -m venv $(VENV)
	$(PYTHON_VENV) -m ensurepip --upgrade
	$(PYTHON_VENV) -m pip install --upgrade pip
	$(PYTHON_VENV) -m pip install -r requirements.txt

.PHONY: run
run:
	$(PYTHON_VENV) main.py

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

RSSI ?= -100
SNR  ?= -15

.PHONY: predict
predict:
	$(PYTHON_VENV) cli.py predict --rssi $(RSSI) --snr $(SNR)