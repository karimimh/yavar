.PHONY: install up down logs build web backend migrate worker beat test test-web test-backend lint format

# ----- Setup -----

install: ## Install frontend and backend dependencies locally
	cd apps/web && npm ci
	cd backend && uv sync
	cd automation/browser && uv sync && uv run playwright install chromium

# ----- Docker (full stack) -----

up: ## Start the complete development stack
	docker compose up -d --build

down: ## Stop all Docker services
	docker compose down

logs: ## Tail logs from all services
	docker compose logs -f

build: ## Rebuild all Docker images
	docker compose build

# ----- Run services locally (outside Docker) -----

web: ## Run the Next.js dev server locally
	cd apps/web && npm run dev

backend: ## Run the Django dev server locally
	cd backend && uv run python manage.py runserver

migrate: ## Run Django migrations
	cd backend && uv run python manage.py migrate

worker: ## Start a Celery worker locally
	cd backend && uv run celery -A config worker --loglevel=info

beat: ## Start Celery Beat locally
	cd backend && uv run celery -A config beat --loglevel=info

# ----- Quality -----

test: test-web test-backend ## Run all tests

test-web: ## Run frontend tests
	cd apps/web && npm test

test-backend: ## Run backend tests
	cd backend && uv run pytest

lint: ## Lint frontend and backend
	cd apps/web && npm run lint && npm run typecheck
	cd backend && uv run ruff check .
	cd automation/browser && uv run ruff check .

format: ## Format frontend and backend code
	cd apps/web && npm run format
	cd backend && uv run ruff format .
	cd automation/browser && uv run ruff format .

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-14s %s\n", $$1, $$2}'
