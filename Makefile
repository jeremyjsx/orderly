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

PYTEST = $(VENV_PYTHON) -m pytest
DOCKER_COMPOSE = docker-compose

.PHONY: venv install lint format format-check run test test-docker clean-test

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

test:
	$(PYTEST) tests/

test-docker:
	@echo "Starting test database container..."
	$(DOCKER_COMPOSE) -f docker-compose.test.yml up -d postgres-test
	@echo "Waiting for database to be ready..."
	@timeout=30; \
	while [ $$timeout -gt 0 ]; do \
		if $(DOCKER_COMPOSE) -f docker-compose.test.yml exec -T postgres-test pg_isready -U test_user > /dev/null 2>&1; then \
			break; \
		fi; \
		sleep 1; \
		timeout=$$((timeout-1)); \
	done; \
	if [ $$timeout -eq 0 ]; then \
		echo "Database failed to start"; \
		$(DOCKER_COMPOSE) -f docker-compose.test.yml down -v; \
		exit 1; \
	fi
	@echo "Running tests..."
	TEST_DATABASE_URL=postgresql+asyncpg://test_user:test_password@localhost:5433/orderly_test $(PYTEST) tests/ || EXIT_CODE=$$?; \
	echo "Cleaning up test container..."; \
	$(DOCKER_COMPOSE) -f docker-compose.test.yml down -v; \
	exit $$EXIT_CODE

clean-test:
	$(DOCKER_COMPOSE) -f docker-compose.test.yml down -v