# Simple commands to run the volunteer management API

.PHONY: help install dev test clean lint format run

# Default target
help:
	@echo "Available commands:"
	@echo "  make install  - Install dependencies"
	@echo "  make dev      - Run development server with auto-reload"
	@echo "  make run      - Run production server"
	@echo "  make test     - Run tests"
	@echo "  make lint     - Check code style"
	@echo "  make format   - Format code"
	@echo "  make clean    - Clean cache files"

# Install dependencies
install:
	pip install -r requirements.txt

# Run development server with auto-reload
dev:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Run production server
run:
	uvicorn src.main:app --host 0.0.0.0 --port 8000

# Run tests
test:
	python -m pytest src/tests/ -v

# Lint code
lint:
	flake8 src/ --max-line-length=100 --ignore=E203,W503

# Format code
format:
	black src/ --line-length=100
	isort src/

# Clean cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete