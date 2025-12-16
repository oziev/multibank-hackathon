.PHONY: help dev install build check clean
.DEFAULT_GOAL := help

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

dev: ## Start dev server
	@pnpm run dev

install: ## Install dependencies
	@pnpm install

build: ## Build production
	@pnpm run build

check: ## Run checks
	@pnpm run check

clean: ## Clean artifacts
	@rm -rf node_modules dist .pnpm-store

docker-dev: ## Docker dev server
	@docker-compose up -d

docker-stop: ## Stop Docker dev
	@docker-compose down

docker-build: ## Build production image
	@docker build --target=production -t bank-frontend .

docker-run: docker-build ## Run production
	@docker run -d -p 80:80 --name bank-frontend bank-frontend

up: docker-dev ## Alias for docker-dev

down: docker-stop ## Alias for docker-stop
