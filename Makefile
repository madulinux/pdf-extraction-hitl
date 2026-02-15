.PHONY: help build up down restart logs clean test volumes

DC := docker compose
DCP := docker compose -f docker-compose.production.yml --env-file .env

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
	$(DC) build

build-prod:
	@echo "Building Docker images..."
	$(DCP) build

# Start containers
up:
	@echo "Starting containers..."
	$(DC) up -d
	@echo ""
	@echo "✅ Services started!"
	@echo ""
	@echo "View logs: make logs"

# Start container production
up-prod:
	@echo "Startin production containers..."
	$(DCP) up -d

	@echo ""
	@echo "✅ Services started!"
	@echo ""
	@echo "View logs: make logs"

# Start with rebuild
up-build:
	@echo "Rebuilding and starting containers..."
	$(DC) up --build -d

up-prod-build:
	@echo "Rebuilding and starting containers..."
	$(DCP) up -d --build


# Stop containers
down:
	@echo "Stopping containers..."
	$(DC) down

down-prod:
	@echo "Stopping production containers..."
	$(DCP) down

# Restart containers
restart:
	@echo "Restarting containers..."
	$(DC) restart

restart-prod:
	@echo "Restarting production containers..."
	$(DCP) restart

# View logs
logs:
	$(DC) logs -f

logs-prod:
	$(DCP) logs -f

# View backend logs
logs-backend:
	$(DC) logs -f backend

logs-backend-prod:
	$(DCP) logs -f backend

# View frontend logs
logs-frontend:
	$(DC) logs -f frontend

logs-frontend-prod:
	$(DCP) logs -f frontend

logs-worker:
	$(DC) logs -f backend-worker

logs-worker-prod:
	$(DCP) logs -f backend-worker

logs-traefik-prod:
	$(DCP) logs -f traefik

# Clean everything
clean:
	@echo "Cleaning up..."
	$(DC) down -v
	@echo "✅ Cleanup complete"

# Run tests
test:
	@echo "Running tests..."
	$(DC) run --rm backend pytest

# Access backend shell
backend:
	$(DC) exec backend sh

backend-prod:
	$(DCP) exec backend sh

# Access frontend shell
frontend:
	$(DC) exec frontend sh

frontend-prod:
	$(DCP) exec frontend sh

worker:
	$(DC) exec backend-worker sh

worker-prod:
	$(DCP) exec backend-worker sh

traefik-prod:
	$(DCP) exec traefik sh

# Show container status
status:
	$(DC) ps

status-prod:
	$(DCP) ps

# Show resource usage
stats:
	docker stats --no-stream

pull:
	$(DC) pull

pull-prod:
	$(DCP) pull

update-prod:
	$(DCP) pull
	$(DCP) up -d

recreate-prod:
	$(DCP) up -d --force-recreate

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
