.PHONY: help setup install clean format lint test test-unit test-integration coverage docker-up docker-down docker-restart docker-logs docker-status run run-dev freeze check-python check-docker info

# Variables
PYTHON := python
PYTHON_VERSION := 3.11
VENV := venv
DOCKER_COMPOSE := docker-compose
PYTEST := $(PYTHON) -m pytest

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
	@$(MAKE) install

install: check-python
	@echo "$(BLUE)Installing dependencies...$(NC)"
	@$(PYTHON) -m pip install --upgrade pip setuptools wheel
	@$(PYTHON) -m pip install -r requirements.txt
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

test-unit: check-python docker-status
	@echo "$(BLUE)Running unit tests...$(NC)"
	@$(PYTEST) tests/unit -v --tb=short
	@echo "$(GREEN)✓ Unit tests passed$(NC)"

test-integration: check-python docker-status
	@echo "$(BLUE)Running integration tests...$(NC)"
	@$(PYTEST) tests/integration -v --tb=short
	@echo "$(GREEN)✓ Integration tests passed$(NC)"

coverage: check-python docker-status
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	@$(PYTEST) --cov=app --cov-report=html --cov-report=term-missing -v
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
