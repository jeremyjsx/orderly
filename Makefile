VENV = venv

ifeq ($(OS),Windows_NT)
	PYTHON = python
	VENV_PYTHON = $(VENV)/Scripts/python.exe
	PIP = $(VENV_PYTHON) -m pip
	UVICORN = $(VENV)/Scripts/uvicorn
	RUFF = $(VENV)/Scripts/ruff
	ALEMBIC = $(VENV)/Scripts/alembic
else
	PYTHON = python3
	VENV_PYTHON = $(VENV)/bin/python
	PIP = $(VENV_PYTHON) -m pip
	UVICORN = $(VENV)/bin/uvicorn
	RUFF = $(VENV)/bin/ruff
	ALEMBIC = $(VENV)/bin/alembic
endif

PORT ?= 8000

PYTEST = $(VENV_PYTHON) -m pytest
DOCKER_COMPOSE = docker compose

.PHONY: venv install lint format format-check run dev dev-down test clean-test docker-build docker-up docker-down docker-logs migrate migrate-down

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

migrate:
	$(ALEMBIC) upgrade head

migrate-down:
	$(ALEMBIC) downgrade -1

dev:
	$(DOCKER_COMPOSE) up -d postgres redis rabbitmq localstack prometheus grafana
	@echo "Infrastructure ready. Run 'make run' to start the API with hot-reload."

test:
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

docker-build:
	$(DOCKER_COMPOSE) build

docker-up:
	$(DOCKER_COMPOSE) up -d

docker-down:
	$(DOCKER_COMPOSE) down

docker-logs:
	$(DOCKER_COMPOSE) logs -f api