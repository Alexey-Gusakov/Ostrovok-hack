.PHONY: help up down build restart logs health test clean

# Default target
help:
	@echo "Hotel Embeddings Application - Makefile Commands"
	@echo "=================================================="
	@echo ""
	@echo "Setup and Environment:"
	@echo "  make setup    - Create .env file from .env.example"
	@echo ""
	@echo "Docker Operations:"
	@echo "  make build    - Build Docker images"
	@echo "  make up       - Start all services"
	@echo "  make down     - Stop all services"
	@echo "  make restart  - Restart all services"
	@echo "  make logs     - Show logs from all services"
	@echo ""
	@echo "Testing and Verification:"
	@echo "  make test     - Run application tests"
	@echo "  make health   - Check application health"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean    - Remove containers, volumes, and images"
	@echo ""

# Setup environment
setup:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✓ Created .env file from .env.example"; \
		echo "⚠️  Please edit .env and add your OPENAI_API_KEY"; \
	else \
		echo "✓ .env file already exists"; \
	fi

# Build Docker images
build:
	@echo "Building Docker images..."
	docker compose build

# Start services
up: setup
	@echo "Starting services..."
	docker compose up -d
	@echo ""
	@echo "✓ Services started!"
	@echo "→ Open http://localhost:8080 in your browser"
	@echo ""
	@echo "View logs with: make logs"
	@echo "Check health with: make health"

# Stop services
down:
	@echo "Stopping services..."
	docker compose down

# Restart services
restart:
	@echo "Restarting services..."
	docker compose restart

# Show logs
logs:
	docker compose logs -f app

# Check health
health:
	@echo "Checking application health..."
	@curl -s http://localhost:8080/health | python3 -m json.tool || echo "✗ Application is not responding"

# Run tests
test:
	@echo "Running application tests..."
	@python3 test_app.py

# Clean up everything
clean:
	@echo "Cleaning up..."
	docker compose down -v
	docker system prune -f
	@echo "✓ Cleanup complete"
