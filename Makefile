.PHONY: dev build test clean seed logs

# Development with hot reload
dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# Production-like build
build:
	docker compose up --build -d

# Stop all services
down:
	docker compose down

# Run backend tests
test-backend:
	cd backend && python3 -m pytest tests/ -v --tb=short

# Run frontend tests
test-frontend:
	cd frontend && npx vitest run

# Run all tests
test: test-backend test-frontend

# View logs
logs:
	docker compose logs -f

# Clean volumes and containers
clean:
	docker compose down -v --remove-orphans
	docker system prune -f

# Database shell
db-shell:
	docker compose exec postgres psql -U monsoonprep -d monsoonprep

# Redis shell
redis-shell:
	docker compose exec redis redis-cli

# Backend shell
api-shell:
	docker compose exec backend python3 -c "import IPython; IPython.start_ipython()"

# Format backend code
format:
	cd backend && python3 -m black src/ tests/
	cd backend && python3 -m isort src/ tests/

# Lint backend
lint:
	cd backend && python3 -m ruff check src/ tests/
