.PHONY: help install lint test build clean run

help: ## Show this help message
	@echo "Packster - Cross-OS package migration helper"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install packster in development mode
	pip install -e ".[dev]"

lint: ## Run linting checks
	ruff check .
	ruff format --check .

format: ## Format code with ruff
	ruff format .

test: ## Run tests
	pytest

test-cov: ## Run tests with coverage
	pytest --cov=packster --cov-report=html --cov-report=term

build: ## Build package
	python -m build

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

run: ## Run packster CLI (shows help)
	packster --help

dev-install: ## Install for development (with all dependencies)
	pip install -e ".[dev]"
	pre-commit install

check: ## Run all checks (lint, test, build)
	make lint
	make test
	make build
