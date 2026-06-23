# Define variables
DOCKER_COMPOSE = docker-compose
BACKEND_DIR = backend
FRONTEND_DIR = frontend

# Install dependencies
install:
	pip install -r $(BACKEND_DIR)/requirements.txt
	cd $(FRONTEND_DIR) && npm install

# Start development environment
dev:
	./scripts/dev.sh

# Build the project
build:
	docker build -t rag-backend $(BACKEND_DIR)
	docker build -t rag-frontend $(FRONTEND_DIR)

# Run tests
test:
	pytest $(BACKEND_DIR)/tests
	cd $(FRONTEND_DIR) && npm test

# Start Docker Compose services
docker-up:
	$(DOCKER_COMPOSE) up -d

# Stop Docker Compose services
docker-down:
	$(DOCKER_COMPOSE) down

# Clean up Docker artifacts
clean:
	$(DOCKER_COMPOSE) down --volumes --remove-orphans
	docker system prune -f