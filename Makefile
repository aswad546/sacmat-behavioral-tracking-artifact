SHELL := /bin/bash
COMPOSE := docker compose -f docker-compose.artifact.yml
COMPOSE_OBS := $(COMPOSE) -f docker-compose.observability.yml
FULL_PROFILES := --profile logingpt --profile crawl --profile sa

.PHONY: help up down full login-only crawl-only analyze-only classify \
        smoke results modal-deploy logs up-obs clean validate

help:
	@echo "up / full       Full pipeline (logingpt + crawl + sa)"
	@echo "down            Stop everything"
	@echo "login-only      Only LoginGPT services"
	@echo "crawl-only      Only VisibleV8 crawler"
	@echo "analyze-only    Only BBSA + vv8-postgres"
	@echo "smoke           20-URL end-to-end smoke test"
	@echo "results         Paper-claim table from multicore_static_info"
	@echo "classify        Run the RF classifier against multicore_static_info"
	@echo "modal-deploy    Deploy Qwen + OS-Atlas to Modal"
	@echo "up-obs          Full pipeline + observability overlay"
	@echo "logs            Tail all logs"
	@echo "validate        docker compose config parse check"

up full:
	$(COMPOSE) $(FULL_PROFILES) up -d

down:
	$(COMPOSE) $(FULL_PROFILES) down

login-only:
	$(COMPOSE) --profile logingpt up -d

crawl-only:
	$(COMPOSE) --profile crawl up -d

analyze-only:
	$(COMPOSE) --profile sa --profile crawl up -d

smoke:
	./scripts/smoke_test.sh

results:
	python scripts/check_results.py

classify:
	docker build -t sacmat/classifier:artifact classifier/
	docker run --rm --network sacmat-behavioral-tracking-artifact_artifact_net \
		-e PGHOST=vv8-postgres -e PGPORT=5432 \
		-e PGUSER=$${POSTGRES_USER:-vv8} -e PGPASSWORD=$${POSTGRES_PASSWORD:-vv8} \
		-e PGDATABASE=$${POSTGRES_DB:-vv8_backend} \
		sacmat/classifier:artifact

modal-deploy:
	modal deploy modal/qwen_app.py
	modal deploy modal/os_atlas_app.py
	@echo "Paste the two URLs above into .env as QWEN_BASE_URL and OS_ATLAS_BASE_URL"

up-obs:
	$(COMPOSE_OBS) $(FULL_PROFILES) --profile observability up -d

logs:
	$(COMPOSE) $(FULL_PROFILES) logs -f --tail=50

validate:
	$(COMPOSE) $(FULL_PROFILES) config > /dev/null && echo "compose config OK"

clean:
	@read -p "Delete ./data/*? [y/N] " ans; [ "$$ans" = "y" ] && rm -rf data/postgres data/mongo data/rabbit data/graphs data/screenshots data/logs data/minio data/vv8 data/bbsa || echo cancelled
