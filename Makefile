# Variables
DOCKER_COMPOSE = docker-compose
PYTHON = python3
NPM = npm

# Install dependencies
install:
	$(PYTHON) -m pip install -r backend/requirements.txt
	cd frontend && $(NPM) install

# Start development environment
dev:
	./scripts/dev.sh

# Build production images
build:
	$(DOCKER_COMPOSE) build

# Run tests
test:
	pytest backend/tests
	cd frontend && $(NPM) test

# Start Docker Compose services
docker-up:
	$(DOCKER_COMPOSE) up -d

# Stop Docker Compose services
docker-down:
	$(DOCKER_COMPOSE) down

# Clean up Docker artifacts
clean:
	$(DOCKER_COMPOSE) down -v --rmi all --remove-orphans