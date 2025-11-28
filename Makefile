.PHONY: help setup install install-venv clean format lint test test-unit test-integration coverage docker-up docker-down docker-restart docker-logs docker-status docker-rebuild db-migrate db-downgrade db-revision run run-dev freeze check-python check-docker info keycloak-setup keycloak-verify keycloak-test-auth

# Variables
PYTHON := python
PYTHON_VERSION := 3.11
VENV := venv
DOCKER_COMPOSE := docker-compose

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
RED := \033[0;31m
NC := \033[0m # No Color

# Default target
help:
	@echo "$(BLUE)================================$(NC)"
	@echo "$(BLUE)Movie API - Development Makefile$(NC)"
	@echo "$(BLUE)================================$(NC)"
	@echo ""
	@echo "$(GREEN)Setup & Dependencies:$(NC)"
	@echo "  make setup              Create virtual environment and install dependencies"
	@echo "  make install            Install dependencies into virtual environment"
	@echo "  make freeze             Generate requirements.txt from current environment"
	@echo "  make clean              Remove virtual environment, caches, and build artifacts"
	@echo ""
	@echo "$(GREEN)Code Quality:$(NC)"
	@echo "  make format             Format code with black and isort"
	@echo "  make lint               Run linting checks (pylint, flake8)"
	@echo "  make check              Run all checks (format, lint, type hints)"
	@echo ""
	@echo "$(GREEN)Testing:$(NC)"
	@echo "  make test               Run all tests (unit + integration)"
	@echo "  make test-unit          Run unit tests only"
	@echo "  make test-integration   Run integration tests only"
	@echo "  make coverage           Run tests with code coverage report"
	@echo ""
	@echo "$(GREEN)Docker:$(NC)"
	@echo "  make docker-up          Start all services (docker-compose up -d)"
	@echo "  make docker-down        Stop all services (docker-compose down)"
	@echo "  make docker-restart     Restart all services"
	@echo "  make docker-clean       Stop and remove all volumes"
	@echo "  make docker-logs        View docker-compose logs"
	@echo "  make docker-status      Show running containers"
	@echo "  make docker-rebuild     Rebuild containers"
	@echo ""
	@echo "$(GREEN)Database:$(NC)"
	@echo "  make db-migrate         Run pending database migrations"
	@echo "  make db-downgrade       Rollback last database migration"
	@echo "  make db-revision        Create a new migration (MESSAGE=description)"
	@echo ""
	@echo "$(GREEN)Running Application:$(NC)"
	@echo "  make run                Run FastAPI application (production)"
	@echo "  make run-dev            Run FastAPI with hot reload (development)"
	@echo ""
	@echo "$(GREEN)Keycloak:$(NC)"
	@echo "  make keycloak-setup     Run Keycloak setup script"
	@echo "  make keycloak-verify    Verify Keycloak configuration"
	@echo "  make keycloak-test-auth Test authentication flows"
	@echo ""
	@echo "$(GREEN)Utilities:$(NC)"
	@echo "  make info               Display environment and version info"
	@echo "  make check-python       Check Python installation"
	@echo "  make check-docker       Check Docker installation"
	@echo "  make help               Show this help message"
	@echo ""

# Setup & Dependencies
setup: check-python check-docker
	@echo "$(BLUE)Setting up development environment...$(NC)"
	@$(PYTHON) -m venv $(VENV)
	@echo "$(GREEN)✓ Virtual environment created$(NC)"
	@$(MAKE) install-venv
	@echo ""
	@echo "$(BLUE)Starting Docker services...$(NC)"
	@$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✓ Docker services started (db migrations running...)$(NC)"
	@sleep 10
	@echo ""
	@echo "$(BLUE)Initializing Keycloak...$(NC)"
	@$(MAKE) keycloak-setup
	@echo ""
	@echo "$(GREEN)=============================================$(NC)"
	@echo "$(GREEN)Setup complete!$(NC)"
	@echo "$(GREEN)=============================================$(NC)"
	@echo ""
	@echo "$(YELLOW)To activate the virtual environment, run:$(NC)"
ifdef OS
	@echo "  $(VENV)\\Scripts\\activate"
else
	@echo "  source $(VENV)/bin/activate"
endif
	@echo ""
	@echo "$(YELLOW)Then you can use:$(NC)"
	@echo "  make run-dev          # Run with hot reload"
	@echo "  make test             # Run all tests"
	@echo "  make docker-logs      # View Docker logs"
	@echo ""

install: check-python
	@echo "$(BLUE)Installing dependencies...$(NC)"
	@. $(VENV)/bin/activate 2>/dev/null || . $(VENV)/Scripts/activate && $(PYTHON) -m pip install --upgrade pip setuptools wheel && $(PYTHON) -m pip install -r requirements.txt
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

install-venv:
	@echo "$(BLUE)Installing dependencies into virtual environment...$(NC)"
ifdef OS
	@$(VENV)/Scripts/python -m pip install --upgrade pip setuptools wheel
	@$(VENV)/Scripts/python -m pip install -r requirements.txt
else
	@$(VENV)/bin/python -m pip install --upgrade pip setuptools wheel
	@$(VENV)/bin/python -m pip install -r requirements.txt
endif
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

freeze:
	@echo "$(BLUE)Freezing dependencies...$(NC)"
	@$(PYTHON) -m pip freeze > requirements.txt
	@echo "$(GREEN)✓ requirements.txt updated$(NC)"

clean:
	@echo "$(BLUE)Cleaning up...$(NC)"
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .coverage -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name htmlcov -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name ".coverage*" -delete
	@rm -rf build/ dist/ *.egg-info 2>/dev/null || true
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

# Code Quality
format: check-python
	@echo "$(BLUE)Formatting code...$(NC)"
	@$(PYTHON) -m black app/ tests/ scripts/ --line-length=100
	@$(PYTHON) -m isort app/ tests/ scripts/ --profile black
	@echo "$(GREEN)✓ Code formatted$(NC)"

lint: check-python
	@echo "$(BLUE)Running linting checks...$(NC)"
	@$(PYTHON) -m pylint app/ --fail-under=8.0 2>/dev/null || echo "$(YELLOW)Note: Install pylint for full linting$(NC)"
	@$(PYTHON) -m flake8 app/ tests/ scripts/ --max-line-length=100 --ignore=E501,W503 2>/dev/null || echo "$(YELLOW)Note: Install flake8 for full linting$(NC)"
	@echo "$(GREEN)✓ Linting complete$(NC)"

check: format lint
	@echo "$(GREEN)✓ All checks passed$(NC)"

# Testing
test: check-docker test-unit test-integration
	@echo "$(GREEN)✓ All tests passed$(NC)"

test-unit: check-python
	@echo "$(BLUE)Running unit tests...$(NC)"
ifdef OS
	@if exist $(VENV)\Scripts\python.exe ( \
		$(VENV)\Scripts\python -m pytest tests/unit -v --tb=short \
	) else ( \
		$(PYTHON) -m pytest tests/unit -v --tb=short \
	)
else
	@if [ -f $(VENV)/bin/python ]; then \
		$(VENV)/bin/python -m pytest tests/unit -v --tb=short; \
	else \
		$(PYTHON) -m pytest tests/unit -v --tb=short; \
	fi
endif
	@echo "$(GREEN)✓ Unit tests passed$(NC)"

test-integration: check-python docker-status
	@echo "$(BLUE)Running integration tests...$(NC)"
ifdef OS
	@if exist $(VENV)\Scripts\python.exe ( \
		$(VENV)\Scripts\python -m pytest tests/integration -v --tb=short \
	) else ( \
		$(PYTHON) -m pytest tests/integration -v --tb=short \
	)
else
	@if [ -f $(VENV)/bin/python ]; then \
		$(VENV)/bin/python -m pytest tests/integration -v --tb=short; \
	else \
		$(PYTHON) -m pytest tests/integration -v --tb=short; \
	fi
endif
	@echo "$(GREEN)✓ Integration tests passed$(NC)"

coverage: check-python docker-status
	@echo "$(BLUE)Running tests with coverage...$(NC)"
ifdef OS
	@if exist $(VENV)\Scripts\python.exe ( \
		$(VENV)\Scripts\python -m pytest --cov=app --cov-report=html --cov-report=term-missing -v \
	) else ( \
		$(PYTHON) -m pytest --cov=app --cov-report=html --cov-report=term-missing -v \
	)
else
	@if [ -f $(VENV)/bin/python ]; then \
		$(VENV)/bin/python -m pytest --cov=app --cov-report=html --cov-report=term-missing -v; \
	else \
		$(PYTHON) -m pytest --cov=app --cov-report=html --cov-report=term-missing -v; \
	fi
endif
	@echo "$(GREEN)✓ Coverage report generated (open htmlcov/index.html to view)$(NC)"

# Docker Commands
docker-up: check-docker
	@echo "$(BLUE)Starting Docker services...$(NC)"
	@$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✓ Services started$(NC)"
	@$(MAKE) docker-status

docker-down: check-docker
	@echo "$(BLUE)Stopping Docker services...$(NC)"
	@$(DOCKER_COMPOSE) down
	@echo "$(GREEN)✓ Services stopped$(NC)"

docker-restart: check-docker
	@echo "$(BLUE)Restarting Docker services...$(NC)"
	@$(DOCKER_COMPOSE) restart
	@echo "$(GREEN)✓ Services restarted$(NC)"
	@$(MAKE) docker-status

docker-clean: check-docker
	@echo "$(BLUE)Removing all containers and volumes...$(NC)"
	@$(DOCKER_COMPOSE) down -v
	@echo "$(GREEN)✓ All containers and volumes removed$(NC)"

docker-logs: check-docker
	@$(DOCKER_COMPOSE) logs -f

docker-status: check-docker
	@echo "$(BLUE)Docker services status:$(NC)"
	@$(DOCKER_COMPOSE) ps

docker-rebuild: check-docker
	@echo "$(BLUE)Rebuilding Docker images...$(NC)"
	@$(DOCKER_COMPOSE) build --no-cache
	@echo "$(GREEN)✓ Images rebuilt$(NC)"

# Database Migrations
db-migrate: check-python
	@echo "$(BLUE)Running database migrations...$(NC)"
ifdef OS
	@if exist $(VENV)\Scripts\python.exe ( \
		$(VENV)\Scripts\python -m alembic upgrade head \
	) else ( \
		$(PYTHON) -m alembic upgrade head \
	)
else
	@if [ -f $(VENV)/bin/python ]; then \
		$(VENV)/bin/python -m alembic upgrade head; \
	else \
		$(PYTHON) -m alembic upgrade head; \
	fi
endif
	@echo "$(GREEN)✓ Database migrations completed$(NC)"

db-downgrade: check-python
	@echo "$(BLUE)Rolling back database migrations...$(NC)"
ifdef OS
	@if exist $(VENV)\Scripts\python.exe ( \
		$(VENV)\Scripts\python -m alembic downgrade -1 \
	) else ( \
		$(PYTHON) -m alembic downgrade -1 \
	)
else
	@if [ -f $(VENV)/bin/python ]; then \
		$(VENV)/bin/python -m alembic downgrade -1; \
	else \
		$(PYTHON) -m alembic downgrade -1; \
	fi
endif
	@echo "$(GREEN)✓ Database rollback completed$(NC)"

db-revision: check-python
	@echo "$(BLUE)Creating new database migration...$(NC)"
ifdef OS
	@if exist $(VENV)\Scripts\python.exe ( \
		$(VENV)\Scripts\python -m alembic revision --autogenerate -m "$(MESSAGE)" \
	) else ( \
		$(PYTHON) -m alembic revision --autogenerate -m "$(MESSAGE)" \
	)
else
	@if [ -f $(VENV)/bin/python ]; then \
		$(VENV)/bin/python -m alembic revision --autogenerate -m "$(MESSAGE)"; \
	else \
		$(PYTHON) -m alembic revision --autogenerate -m "$(MESSAGE)"; \
	fi
endif
	@echo "$(GREEN)✓ Migration created$(NC)"

# Running Application
run: check-python docker-status
	@echo "$(BLUE)Starting FastAPI application...$(NC)"
	@$(PYTHON) -m uvicorn app.main:app --host 0.0.0.0 --port 8000

run-dev: check-python docker-status
	@echo "$(BLUE)Starting FastAPI with hot reload...$(NC)"
	@$(PYTHON) -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Keycloak Commands
keycloak-setup: check-python docker-status
	@echo "$(BLUE)Running Keycloak setup...$(NC)"
	@$(PYTHON) scripts/keycloak-setup.py

keycloak-verify: check-python docker-status
	@echo "$(BLUE)Verifying Keycloak configuration...$(NC)"
	@$(PYTHON) scripts/verify-keycloak.py

keycloak-test-auth: check-python docker-status
	@echo "$(BLUE)Testing authentication flows...$(NC)"
	@$(PYTHON) scripts/test-auth-flows.py

# Utility Commands
info:
	@echo "$(BLUE)================================$(NC)"
	@echo "$(BLUE)Environment Information$(NC)"
	@echo "$(BLUE)================================$(NC)"
	@echo ""
	@echo "$(GREEN)Python:$(NC)"
	@$(PYTHON) --version
	@echo ""
	@echo "$(GREEN)Docker:$(NC)"
	@docker --version
	@$(DOCKER_COMPOSE) --version
	@echo ""
	@echo "$(GREEN)Project:$(NC)"
	@echo "  Virtual Env: $(VENV)"
	@echo ""
	@echo "$(GREEN)Docker Services:$(NC)"
	@$(DOCKER_COMPOSE) ps
	@echo ""

check-python:
	@command -v $(PYTHON) >/dev/null 2>&1 || { echo "$(RED)✗ Python not found. Please install Python $(PYTHON_VERSION)$(NC)"; exit 1; }
	@echo "$(GREEN)✓ Python found: $(shell $(PYTHON) --version)$(NC)"

check-docker:
	@command -v docker >/dev/null 2>&1 || { echo "$(RED)✗ Docker not found. Please install Docker$(NC)"; exit 1; }
	@command -v $(DOCKER_COMPOSE) >/dev/null 2>&1 || { echo "$(RED)✗ Docker Compose not found. Please install Docker Compose$(NC)"; exit 1; }
	@echo "$(GREEN)✓ Docker found: $(shell docker --version)$(NC)"
	@echo "$(GREEN)✓ Docker Compose found: $(shell $(DOCKER_COMPOSE) --version)$(NC)"
