PYTHON := python3.12
VENV := .venv
PIP := $(VENV)/bin/pip
PYTHON_VENV := $(VENV)/bin/python

.PHONY: help
help:
	@echo "Available commands:"
	@echo "  make install   Create virtualenv & install dependencies"
	@echo "  make run       Run application"
	@echo "  make freeze    Update requirements.txt"
	@echo "  make clean     Remove virtual environment"

.PHONY: install
install:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

.PHONY: run
run:
	$(PYTHON_VENV) main.py

.PHONY: freeze
freeze:
	$(PIP) freeze > requirements.txt

.PHONY: clean
clean:
	rm -rf $(VENV)