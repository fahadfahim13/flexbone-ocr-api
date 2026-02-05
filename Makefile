.PHONY: install dev test lint format type-check security run docker-build docker-run clean

install:
	pip install -r requirements.txt

dev:
	pip install -r requirements-dev.txt
	pre-commit install

test:
	pytest tests/ -v --cov=app --cov-report=term-missing

test-cov:
	pytest tests/ -v --cov=app --cov-report=html
	@echo "Coverage report: htmlcov/index.html"

lint:
	ruff check app/ tests/

lint-fix:
	ruff check app/ tests/ --fix

format:
	black app/ tests/

type-check:
	mypy app/

security:
	bandit -r app/ -ll

check: lint type-check security test

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

docker-build:
	docker build -t flexbone-ocr-api:latest .

docker-run:
	docker-compose up

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache .coverage htmlcov .mypy_cache .ruff_cache
