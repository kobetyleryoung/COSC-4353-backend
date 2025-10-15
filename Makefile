# COSC-4353 Backend Makefile
# Simple commands to run the volunteer management API

.PHONY: help install dev test test-unit test-integration test-coverage clean lint format run

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