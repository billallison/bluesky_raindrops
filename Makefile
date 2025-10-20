# Makefile for Raindrop to Bluesky Bot
# Provides convenient shortcuts for common Docker operations

.PHONY: help build up down restart logs logs-live status clean test shell exec

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Build the Docker container
	docker-compose build

up: ## Start the container in detached mode
	docker-compose up -d

down: ## Stop and remove the container
	docker-compose down

restart: ## Restart the container
	docker-compose restart

logs: ## Show last 50 log lines
	docker-compose logs --tail=50

logs-live: ## Follow logs in real-time
	docker-compose logs -f

status: ## Show container status
	docker-compose ps

clean: ## Stop container and remove images
	docker-compose down --rmi all

rebuild: ## Rebuild and restart the container
	docker-compose up -d --build

test: ## Run the script once for testing
	docker-compose exec bluesky-raindrops-bot python /app/raindrop_to_bluesky.py

shell: ## Open a shell in the running container
	docker-compose exec bluesky-raindrops-bot /bin/bash

cron: ## Show cron schedule
	docker-compose exec bluesky-raindrops-bot crontab -l

app-logs: ## View application log file
	tail -f logs/bluesky_raindrops.log

cron-logs: ## View cron execution logs
	docker-compose exec bluesky-raindrops-bot cat /app/logs/cron.log

env-check: ## Verify .env file exists
	@if [ ! -f .env ]; then \
		echo "❌ .env file not found!"; \
		echo "Run: cp .env.example .env"; \
		echo "Then edit .env with your credentials"; \
		exit 1; \
	else \
		echo "✅ .env file exists"; \
	fi

deploy: env-check build up ## Full deployment (check env, build, start)
	@echo "✅ Deployment complete!"
	@echo "View logs with: make logs-live"
