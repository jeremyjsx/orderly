VENV = venv

ifeq ($(OS),Windows_NT)
	PYTHON = python
	VENV_PYTHON = $(VENV)/Scripts/python.exe
	PIP = $(VENV_PYTHON) -m pip
	UVICORN = $(VENV)/Scripts/uvicorn
	RUFF = $(VENV)/Scripts/ruff
else
	PYTHON = python3
	VENV_PYTHON = $(VENV)/bin/python
	PIP = $(VENV_PYTHON) -m pip
	UVICORN = $(VENV)/bin/uvicorn
	RUFF = $(VENV)/bin/ruff
endif

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