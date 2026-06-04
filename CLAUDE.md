# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Environment
make venv          # Create Python virtual environment
make install       # Install dependencies

# Development
make dev           # Start infrastructure only (Postgres, Redis, RabbitMQ, LocalStack, Prometheus, Grafana)
make run           # Start API with hot-reload on :8000
alembic upgrade head  # Apply database migrations

# Quality
make lint          # Check with Ruff (rules: E, F, I, B, UP)
make format        # Fix with Ruff
make format-check  # Verify formatting without changes

# Testing
make test          # Run pytest against isolated test database (docker-compose.test.yml)

# Docker
make docker-build  # Build API image
make docker-up     # Start all services
make docker-down   # Stop all services
```

To run a single test: `pytest tests/test_<module>.py::test_function_name -v`

## Architecture

**Orderly** is a FastAPI e-commerce backend (Python 3.13, SQLAlchemy 2.0 async, PostgreSQL 16).

### Layer structure

```
main.py                    # App factory, lifespan (startup/shutdown hooks)
api/router.py              # Top-level router aggregating all module routers
modules/<name>/            # Feature modules (auth, users, products, categories, cart, orders, health)
  router.py                # FastAPI routes
  service.py               # Business logic
  schemas.py               # Pydantic request/response models
  dependencies.py          # FastAPI dependency injections
core/                      # Cross-cutting concerns
db/                        # SQLAlchemy models, session factory, migrations (Alembic)
events/                    # RabbitMQ consumer workers (orders, payments)
```

### Key architectural decisions

**Database sessions** are injected via FastAPI dependencies (`db/session.py` → `AsyncSession`). Services receive the session as a parameter — never import or create sessions directly inside service functions.

**Authentication** uses JWT access + refresh token pairs. Refresh tokens are stored in Redis for revocation. Token validation is a dependency (`core/security.py`) injected into protected routes.

**Async event processing**: RabbitMQ TOPIC exchange with dead-letter queues (DLX). The `events/` workers run as separate processes, not as part of the main API. Payment processing (`events/payments/`) is intentionally decoupled from order creation.

**Real-time order tracking** uses WebSockets (`/ws/{order_id}`) managed by a singleton `WebSocketConnectionManager`. Role-based access (ADMIN, USER, DRIVER) is enforced at the WS connection level.

**Rate limiting** is Redis-backed with a sliding window algorithm. Two scopes: global IP-based middleware (`core/middleware.py`) and per-endpoint auth rate limits (`core/rate_limit.py`).

**S3 / file uploads** go through `core/s3.py` (aioboto3). In dev, LocalStack emulates S3 on port 4566.

### Infrastructure services (docker-compose.yml)

| Service | Port | Purpose |
|---|---|---|
| PostgreSQL 16 | 5432 | Primary database |
| Redis 7 | 6379 | Token storage, rate limiting, caching |
| RabbitMQ 3 | 5672 / 15672 | Async event queue (mgmt UI on 15672) |
| LocalStack | 4566 | S3 emulation |
| Prometheus | 9090 | Metrics |
| Grafana | 3001 | Dashboards (admin / orderly) |

### Configuration

All settings are Pydantic `BaseSettings` in `core/config.py`, sourced from environment variables. Copy `.env.example` to `.env` to get started. Key groups: `JWT_*`, `DATABASE_URL`, `REDIS_URL`, `RABBITMQ_URL`, `AWS_*` (or LocalStack endpoint), `RATE_LIMIT_*`.

### Order state machine

Orders move through: `pending → processing → shipped → delivered` (with `cancelled` as a terminal state). State transitions are enforced in `modules/orders/service.py`; invalid transitions raise HTTP 422.
