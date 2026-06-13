.PHONY: up down build logs restart clean help

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

up: ## Start all services
	docker-compose up -d

down: ## Stop all services
	docker-compose down

build: ## Build all services
	docker-compose build

logs: ## Show logs from all services
	docker-compose logs -f

logs-api: ## Show logs from backend-api
	docker-compose logs -f backend-api

logs-worker: ## Show logs from graph-worker
	docker-compose logs -f graph-worker

restart: ## Restart all services
	docker-compose restart

clean: ## Stop and remove all containers, volumes, and networks
	docker-compose down -v

rebuild: ## Rebuild and restart all services
	docker-compose down
	docker-compose up --build -d

ps: ## Show running containers
	docker-compose ps
