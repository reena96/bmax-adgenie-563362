.PHONY: help install run test coverage migrate migrate-create migrate-upgrade migrate-downgrade lint format clean

# Default target
help:
	@echo "Available commands:"
	@echo "  make install         - Install dependencies"
	@echo "  make run            - Run development server"
	@echo "  make test           - Run tests"
	@echo "  make coverage       - Run tests with coverage"
	@echo "  make migrate        - Run database migrations"
	@echo "  make migrate-create - Create a new migration"
	@echo "  make migrate-upgrade - Apply migrations"
	@echo "  make migrate-downgrade - Rollback last migration"
	@echo "  make lint           - Run linting"
	@echo "  make format         - Format code"
	@echo "  make clean          - Clean up temporary files"

# Install dependencies
install:
	pip install -r requirements-dev.txt

# Run development server
run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
test:
	pytest

# Run tests with coverage
coverage:
	pytest --cov=app --cov-report=html --cov-report=term

# Run all migrations
migrate: migrate-upgrade

# Create a new migration
migrate-create:
	@read -p "Enter migration message: " message; \
	alembic revision --autogenerate -m "$$message"

# Apply migrations
migrate-upgrade:
	alembic upgrade head

# Rollback last migration
migrate-downgrade:
	alembic downgrade -1

# Run linting
lint:
	flake8 app tests
	mypy app

# Format code
format:
	black app tests

# Clean up temporary files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
