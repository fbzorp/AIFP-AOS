.PHONY: up down logs test migrate verify

DOCKER_COMPOSE = docker compose -f docker-compose.dev.yml

up:
	$(DOCKER_COMPOSE) up -d --build

down:
	$(DOCKER_COMPOSE) down

logs:
	$(DOCKER_COMPOSE) logs -f

test:
	$(DOCKER_COMPOSE) exec -T api uv run pytest tests/ -v

migrate:
	$(DOCKER_COMPOSE) exec -T api uv run alembic upgrade head

verify:
	./scripts/verify_day7.sh
