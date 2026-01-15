PYTHON = python3
VENV = venv
PIP = $(VENV)/bin/pip
UVICORN = $(VENV)/bin/uvicorn
RUFF = $(VENV)/bin/ruff
PORT ?= 8000

.PHONY: venv install lint format format-check run

venv:
	$(PYTHON) -m venv $(VENV)

install:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

lint:
	$(RUFF) check .

format:
	$(RUFF) format .
	$(RUFF) check --fix .

format-check:
	$(RUFF) format --check .
	$(RUFF) check .

run:
	$(UVICORN) app.main:app --reload --port $(PORT)