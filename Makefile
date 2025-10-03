.PHONY: db-upgrade seed-experiments seed-experiments-reset compose-clean compose-db-up compose-up compose-debug compose-debug-bg auth-token hey-setup hey hey-filters-di hey-filters-inline hey-filters-di-noquery hey-filters-inline-mw hey-matrix hey-matrix-all

SHELL := /bin/bash

SEED_ARGS ?=

ENV_FILE ?= .env
FIRST_SUPERUSER ?= $(strip $(shell sed -n 's/^FIRST_SUPERUSER=//p' $(ENV_FILE)))
FIRST_SUPERUSER_PASSWORD ?= $(strip $(shell sed -n 's/^FIRST_SUPERUSER_PASSWORD=//p' $(ENV_FILE)))

HEY_CMD ?= hey
HEY_BASE_URL ?= http://localhost:8000
HEY_PATH ?= /api/v1/experiments/connection-lifetime/filters-di
HEY_CONCURRENCY ?= 50
HEY_DURATION ?= 30s
HEY_RPS ?=
HEY_METHOD ?=
HEY_HEADERS ?=
HEY_EXTRA_ARGS ?=
HEY_AUTH_TOKEN ?=
HEY_LOG_DIR ?= logs/hey
HEY_LABEL ?=
HEY_MATRIX_CONCURRENCY ?= 5 10 25 50 75 100 250 500 1000

db-upgrade:
	cd backend && uv run alembic upgrade head

seed-experiments: db-upgrade
	cd backend && uv run python scripts/seed_experiments.py $(SEED_ARGS)

seed-experiments-reset: db-upgrade
	cd backend && uv run python scripts/seed_experiments.py --reset $(SEED_ARGS)

auth-token:
	@USER=$${USERNAME:-$(FIRST_SUPERUSER)}; \
	PASS=$${PASSWORD:-$(FIRST_SUPERUSER_PASSWORD)}; \
	if [[ -z "$$USER" || -z "$$PASS" ]]; then \
	  echo ""; \
	  exit 0; \
	fi; \
	curl -s -X POST "$(HEY_BASE_URL)/api/v1/login/access-token" \
	  -H 'Content-Type: application/x-www-form-urlencoded' \
	  -d "username=$$USER&password=$$PASS" | jq -r '.access_token'

hey-setup:
	@mkdir -p $(HEY_LOG_DIR)

hey: hey-setup
	@timestamp=$$(date "+%Y%m%d-%H%M%S"); \
	path_tag=$$(printf "%s" "$(HEY_PATH)" | tr -c 'A-Za-z0-9' '-' | sed 's/^-*//'); \
	[[ -n "$$path_tag" ]] || path_tag="root"; \
	if [[ -n "$(HEY_LABEL)" ]]; then \
	    label_tag=$$(printf "%s" "$(HEY_LABEL)" | tr -c 'A-Za-z0-9' '-' | sed 's/^-*//;s/-*$$//'); \
	    [[ -z "$$label_tag" ]] || path_tag="$$label_tag-$$path_tag"; \
	fi; \
	log_file="$(HEY_LOG_DIR)/$${path_tag}-$${timestamp}.json"; \
	url="$(HEY_BASE_URL)$(HEY_PATH)"; \
	cmd=( "$(HEY_CMD)" ); \
	if [[ -n "$(HEY_METHOD)" ]]; then cmd+=( "-m" "$(HEY_METHOD)" ); fi; \
	cmd+=( "-c" "$(HEY_CONCURRENCY)" "-z" "$(HEY_DURATION)" ); \
	if [[ -n "$(HEY_RPS)" ]]; then cmd+=( "-q" "$(HEY_RPS)" ); fi; \
	auth_token="$(HEY_AUTH_TOKEN)"; \
	if [[ -z "$$auth_token" ]]; then \
	  auth_token="$$( $(MAKE) --no-print-directory auth-token || true )"; \
	fi; \
	auth_token=$$(printf %s "$$auth_token"); \
	if [[ "$$auth_token" == "null" ]]; then auth_token=""; fi; \
	if [[ -n "$$auth_token" ]]; then \
	  cmd+=( "-H" "Authorization: Bearer $$auth_token" ); \
	fi; \
	if [[ -n "$(HEY_HEADERS)" ]]; then \
	    while IFS= read -r line; do [[ -z "$$line" ]] || cmd+=($$line); done <<< "$(HEY_HEADERS)"; \
	fi; \
	if [[ -n "$(HEY_EXTRA_ARGS)" ]]; then \
	    while IFS= read -r line; do [[ -z "$$line" ]] || cmd+=($$line); done <<< "$(HEY_EXTRA_ARGS)"; \
	fi; \
	cmd+=( "$$url" ); \
	display_cmd_str="$(HEY_CMD)"; \
	if [[ -n "$(HEY_METHOD)" ]]; then display_cmd_str+=" -m $(HEY_METHOD)"; fi; \
	display_cmd_str+=" -c $(HEY_CONCURRENCY) -z $(HEY_DURATION)"; \
	if [[ -n "$(HEY_RPS)" ]]; then display_cmd_str+=" -q $(HEY_RPS)"; fi; \
	if [[ -n "$$auth_token" ]]; then display_cmd_str+=" -H Authorization: Bearer ********"; fi; \
	if [[ -n "$(HEY_HEADERS)" ]]; then display_cmd_str+=" $(HEY_HEADERS)"; fi; \
	if [[ -n "$(HEY_EXTRA_ARGS)" ]]; then display_cmd_str+=" $(HEY_EXTRA_ARGS)"; fi; \
	display_cmd_str+=" $$url"; \
	tmp_output=$$(mktemp); \
	echo "Running: $$display_cmd_str"; \
	echo "Logging to: $$log_file"; \
	set -o pipefail; \
	"$${cmd[@]}" | tee "$$tmp_output"; \
	status=$${PIPESTATUS[0]}; \
	if [[ -n "$$auth_token" ]]; then has_auth=1; else has_auth=0; fi; \
	python3 backend/scripts/hey_to_json.py \
	    --input "$$tmp_output" \
	    --output "$$log_file" \
	    --status "$$status" \
	    --timestamp "$$timestamp" \
	    --display-command "$$display_cmd_str" \
	    --base-url "$(HEY_BASE_URL)" \
	    --path "$(HEY_PATH)" \
	    --url "$$url" \
	    --concurrency "$(HEY_CONCURRENCY)" \
	    --duration "$(HEY_DURATION)" \
	    --rps "$(HEY_RPS)" \
	    --method "$(HEY_METHOD)" \
	    --headers "$(HEY_HEADERS)" \
	    --extra-args "$(HEY_EXTRA_ARGS)" \
	    --label "$(HEY_LABEL)" \
	    --has-auth "$$has_auth"; \
	rm -f "$$tmp_output"; \
	echo "Saved log: $$log_file"; \
	echo "hey exit code: $$status"; \
	exit $$status

hey-filters-di: HEY_PATH=/api/v1/experiments/connection-lifetime/filters-di
hey-filters-di: hey

hey-filters-inline: HEY_PATH=/api/v1/experiments/connection-lifetime/filters-inline
hey-filters-inline: hey

hey-filters-di-noquery: HEY_PATH=/api/v1/experiments/connection-lifetime/filters-di-noquery
hey-filters-di-noquery: hey

hey-filters-inline-mw: HEY_PATH=/api/v1/experiments/connection-lifetime/filters-inline-mw
hey-filters-inline-mw: hey

hey-matrix: hey-setup
	@for concurrency in $(HEY_MATRIX_CONCURRENCY); do \
		echo "\n>>> Running matrix step concurrency=$$concurrency"; \
		$(MAKE) --no-print-directory hey HEY_CONCURRENCY=$$concurrency HEY_LABEL=concurrency-$$concurrency HEY_AUTH_TOKEN="$(HEY_AUTH_TOKEN)" HEY_BASE_URL="$(HEY_BASE_URL)" HEY_PATH="$(HEY_PATH)" HEY_DURATION="$(HEY_DURATION)" HEY_RPS="$(HEY_RPS)" HEY_METHOD="$(HEY_METHOD)" HEY_HEADERS="$(HEY_HEADERS)" HEY_EXTRA_ARGS="$(HEY_EXTRA_ARGS)" || exit $$?; \
	done

hey-matrix-all:
	$(MAKE) --no-print-directory hey-matrix HEY_PATH=/api/v1/experiments/connection-lifetime/filters-di
	$(MAKE) --no-print-directory hey-matrix HEY_PATH=/api/v1/experiments/connection-lifetime/filters-inline
	$(MAKE) --no-print-directory hey-matrix HEY_PATH=/api/v1/experiments/connection-lifetime/filters-di-noquery
	$(MAKE) --no-print-directory hey-matrix HEY_PATH=/api/v1/experiments/connection-lifetime/filters-inline-mw

compose-clean:
	docker compose down --volumes --remove-orphans

compose-db-up:
	docker compose up -d db

compose-up: compose-db-up db-upgrade
	docker compose up backend

compose-debug: compose-db-up db-upgrade
	docker compose --profile debug up backend-debug

compose-debug-bg: compose-db-up db-upgrade
	docker compose --profile debug up -d backend-debug
