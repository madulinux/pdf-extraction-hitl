.PHONY: help build up down restart logs clean test

# Default target
help:
	@echo "PDF Extraction HITL - Docker Commands"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  build      - Build all Docker images"
	@echo "  up         - Start all containers"
	@echo "  down       - Stop all containers"
	@echo "  restart    - Restart all containers"
	@echo "  logs       - View container logs"
	@echo "  clean      - Remove containers and volumes"
	@echo "  test       - Run tests"
	@echo "  backend    - Access backend shell"
	@echo "  frontend   - Access frontend shell"
	@echo "  status     - Show container status"
	@echo ""

# Build images
build:
	@echo "Building Docker images..."
	docker-compose build

# Start containers
up:
	@echo "Starting containers..."
	docker-compose up -d
	@echo ""
	@echo "✅ Services started!"
	@echo "Frontend: http://localhost:3000"
	@echo "Backend:  http://localhost:5000"
	@echo ""
	@echo "View logs: make logs"

# Start with rebuild
up-build:
	@echo "Rebuilding and starting containers..."
	docker-compose up --build -d

# Stop containers
down:
	@echo "Stopping containers..."
	docker-compose down

# Restart containers
restart:
	@echo "Restarting containers..."
	docker-compose restart

# View logs
logs:
	docker-compose logs -f

# View backend logs
logs-backend:
	docker-compose logs -f backend

# View frontend logs
logs-frontend:
	docker-compose logs -f frontend

# Clean everything
clean:
	@echo "Cleaning up..."
	docker-compose down -v
	@echo "✅ Cleanup complete"

# Run tests
test:
	@echo "Running tests..."
	docker-compose run --rm backend pytest

# Access backend shell
backend:
	docker-compose exec backend bash

# Access frontend shell
frontend:
	docker-compose exec frontend sh

# Show container status
status:
	docker-compose ps

# Show resource usage
stats:
	docker stats --no-stream

# Backup data
backup:
	@echo "Creating backup..."
	tar -czf backup-$$(date +%Y%m%d-%H%M%S).tar.gz \
		backend/data \
		backend/experiments \
		backend/models
	@echo "✅ Backup created"

# Development mode (with hot reload)
dev:
	@echo "Starting in development mode..."
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
