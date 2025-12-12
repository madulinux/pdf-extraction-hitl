.PHONY: help build up down restart logs clean test volumes

# Default target
help:
	@echo "PDF Extraction HITL - Docker Commands"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Container Management:"
	@echo "  build           - Build all Docker images"
	@echo "  up              - Start all containers"
	@echo "  down            - Stop all containers"
	@echo "  restart         - Restart all containers"
	@echo "  logs            - View container logs"
	@echo "  status          - Show container status"
	@echo ""
	@echo "Access:"
	@echo "  backend         - Access backend shell"
	@echo "  frontend        - Access frontend shell"
	@echo ""
	@echo "Volume Management:"
	@echo "  volumes         - List Docker volumes"
	@echo "  volumes-inspect - Inspect volume details"
	@echo "  volumes-backup  - Backup all volumes"
	@echo "  volumes-clean   - Remove all volumes (DANGER!)"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean           - Remove containers and volumes"
	@echo "  backup          - Backup local data"
	@echo "  test            - Run tests"
	@echo ""

# Build images
build:
	@echo "Building Docker images..."
	docker compose build

# Start containers
up:
	@echo "Starting containers..."
	docker compose up -d
	@echo ""
	@echo "✅ Services started!"
	@echo ""
	@echo "View logs: make logs"

# Start with rebuild
up-build:
	@echo "Rebuilding and starting containers..."
	docker compose up --build -d

# Stop containers
down:
	@echo "Stopping containers..."
	docker compose down

# Restart containers
restart:
	@echo "Restarting containers..."
	docker compose restart

# View logs
logs:
	docker compose logs -f

# View backend logs
logs-backend:
	docker compose logs pdf-extraction-backend -f

# View frontend logs
logs-frontend:
	docker compose logs pdf-extraction-frontend -f

# Clean everything
clean:
	@echo "Cleaning up..."
	docker compose down -v
	@echo "✅ Cleanup complete"

# Run tests
test:
	@echo "Running tests..."
	docker compose run --rm pdf-extraction-backend pytest

# Access backend shell
backend:
	docker exec -it pdf-extraction-backend /bin/bash

# Access frontend shell
frontend:
	docker exec -it pdf-extraction-frontend sh

# Show container status
status:
	docker compose ps

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
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up

# Volume management
volumes:
	@echo "Docker Volumes:"
	@docker volume ls | grep pdf-extraction

volumes-inspect:
	@echo "Inspecting volumes..."
	@docker volume inspect pdf-extraction-hitl_backend-data
	@docker volume inspect pdf-extraction-hitl_backend-experiments
	@docker volume inspect pdf-extraction-hitl_backend-models
	@docker volume inspect pdf-extraction-hitl_backend-uploads

volumes-backup:
	@echo "Backing up volumes..."
	@mkdir -p backups
	@docker run --rm \
		-v pdf-extraction-hitl_backend-data:/data \
		-v pdf-extraction-hitl_backend-experiments:/experiments \
		-v pdf-extraction-hitl_backend-models:/models \
		-v $$(pwd)/backups:/backup \
		alpine tar czf /backup/volumes-backup-$$(date +%Y%m%d-%H%M%S).tar.gz /data /experiments /models
	@echo "✅ Backup created in ./backups/"

volumes-clean:
	@echo "⚠️  This will delete all Docker volumes!"
	@echo "Press Ctrl+C to cancel, or Enter to continue..."
	@read confirm
	docker compose down -v
	@echo "✅ Volumes cleaned"
