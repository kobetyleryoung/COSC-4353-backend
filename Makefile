# COSC-4353 Backend Makefile
# Simple commands to run the volunteer management API

.PHONY: help install dev test test-unit test-integration test-coverage clean lint format run db-init db-drop db-reset db-check db-up db-down db-logs

# Default target
help:
	@echo "Available commands:"
	@echo "  make install       - Install dependencies"
	@echo "  make dev          - Run development server with auto-reload"
	@echo "  make run          - Run production server"
	@echo "  make test         - Run all tests with coverage (requires 80%+)"
	@echo "  make test-unit    - Run unit tests only"
	@echo "  make test-coverage - Run tests and generate coverage report"
	@echo "  make test-html    - Generate HTML coverage report"
	@echo "  make lint         - Check code style"
	@echo "  make format       - Format code"
	@echo "  make clean        - Clean cache files"
	@echo ""
	@echo "Database commands:"
	@echo "  make db-up        - Start PostgreSQL database in Docker"
	@echo "  make db-down      - Stop PostgreSQL database"
	@echo "  make db-logs      - View database logs"
	@echo "  make db-init      - Initialize database tables"
	@echo "  make db-drop      - Drop all database tables (WARNING: destructive!)"
	@echo "  make db-reset     - Drop and recreate all tables (WARNING: destructive!)"
	@echo "  make db-check     - Check database connection"

# Install dependencies
install:
	pip install -r requirements.txt

# Run development server with auto-reload
dev:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Run production server
run:
	uvicorn src.main:app --host 0.0.0.0 --port 8000

# Run all tests with coverage requirement (80%+)
test:
	python -m pytest src/tests/ -v --cov=src --cov-fail-under=80 --cov-report=term-missing

# Run unit tests only
test-unit:
	python -m pytest src/tests/ -v -m "unit or not integration"

# Run tests with detailed coverage
test-coverage:
	python -m pytest src/tests/ -v --cov=src --cov-report=term-missing --cov-report=xml

# Generate HTML coverage report
test-html:
	python -m pytest src/tests/ -v --cov=src --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

# Lint code
lint:
	flake8 src/ --max-line-length=100 --ignore=E203,W503

# Format code
format:
	black src/ --line-length=100
	isort src/

# Clean cache files and coverage reports
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf htmlcov/
	rm -f coverage.xml
	rm -rf .coverage
	rm -rf .pytest_cache/

# Database commands
db-up:
	docker compose -f docker/docker-compose.yml up -d
	@echo "Waiting for database to be ready..."
	@sleep 3
	@echo "PostgreSQL is running on port 5432"

db-down:
	docker compose -f docker/docker-compose.yml down

db-logs:
	docker compose -f docker/docker-compose.yml logs -f postgres

db-init:
	./venv/bin/python -c "from src.repositories.database import DatabaseManager; mgr = DatabaseManager(); mgr.initialize()"

db-drop:
	@echo "WARNING: This will delete all data in the database!"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	./venv/bin/python -c "from src.repositories.database import DatabaseManager, drop_tables; mgr = DatabaseManager(); mgr.initialize(create_tables_if_not_exist=False); drop_tables(mgr.get_engine())"

db-reset:
	@echo "WARNING: This will delete all data and recreate the database!"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	./venv/bin/python -c "from src.repositories.database import DatabaseManager, drop_tables, create_tables; mgr = DatabaseManager(); mgr.initialize(create_tables_if_not_exist=False); drop_tables(mgr.get_engine()); create_tables(mgr.get_engine())"

db-check:
	./venv/bin/python -c "from src.repositories.database import DatabaseManager, check_database_connection; mgr = DatabaseManager(); mgr.initialize(create_tables_if_not_exist=False); print('Database connection:', 'OK' if check_database_connection(mgr.get_engine()) else 'FAILED')"