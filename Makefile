.PHONY: seed-experiments seed-experiments-reset compose-clean compose-debug compose-debug-bg

SEED_ARGS ?=

seed-experiments:
	cd backend && uv run python scripts/seed_experiments.py $(SEED_ARGS)

seed-experiments-reset:
	cd backend && uv run python scripts/seed_experiments.py --reset $(SEED_ARGS)

compose-clean:
	docker compose down --volumes --remove-orphans

compose-debug:
	docker compose --profile debug up backend-debug

compose-debug-bg:
	docker compose --profile debug up -d backend-debug
