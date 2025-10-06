SHELL := /bin/bash

APP ?= app.main:app
HOST ?= 0.0.0.0
PORT ?= 8000
BASE ?= http://localhost:$(PORT)
TOKEN ?= dev-token

DB_POOL_SIZE ?= 10
DB_MAX_OVERFLOW ?= 10
DB_POOL_TIMEOUT ?= 30.0
ANYIO_TOKENS ?= 40

DURATION ?= 30s
CONC ?= 5 25 50 100 250 500 1000
QPS ?=
HEADERS := -H "Authorization: Bearer $(TOKEN)"

ENDPOINTS := \
	/api/v1/exp/inline-sync/filters \
	/api/v1/exp/di-sync/good \
	/api/v1/exp/di-sync/good-inline \
	/api/v1/exp/di-sync/good-direct \
	/api/v1/exp/di-sync/factory \
	/api/v1/exp/mw-sync/filters \
	/api/v1/exp/mw-sync/filters-factory \
	/api/v1/exp/async/di \
	/api/v1/exp/async/factory \
	/api/v1/exp/pool/stats \
	/api/v1/exp/di-sync/leak \
	/api/v1/exp/di-sync/nocache \
	/api/v1/exp/di-sync/manual-next \
	/api/v1/exp/mw-sync-leak/filters \
	/api/v1/exp/async/bridge \
	/api/v1/exp/async/loop-blocking \
	/api/v1/exp/longhold/2

LOG_ROOT := logs
RUN ?= default
LOG_DIR := $(LOG_ROOT)/$(RUN)
BACKEND_DIR := backend
UV := uv
HEY := hey

.PHONY: compose-up compose-down compose-logs compose-rebuild
compose-up:
	docker compose up --build -d db backend

compose-down:
	docker compose down --remove-orphans

compose-logs:
	docker compose logs -f backend

compose-rebuild:
	docker compose up --build backend

.PHONY: run
run:
	cd $(BACKEND_DIR) && \
		POSTGRES_SERVER=localhost \
		DB_POOL_SIZE=$(DB_POOL_SIZE) \
		DB_MAX_OVERFLOW=$(DB_MAX_OVERFLOW) \
		DB_POOL_TIMEOUT=$(DB_POOL_TIMEOUT) \
		ANYIO_TOKENS=$(ANYIO_TOKENS) \
		$(UV) run uvicorn $(APP) --host $(HOST) --port $(PORT) --workers 1

EP ?= /api/v1/exp/inline-sync/filters

.PHONY: sweep
sweep:
	@ep_dir="$(LOG_DIR)/$(subst /,-,$(EP))"; \
	mkdir -p "$$ep_dir"; \
	for c in $(CONC); do \
		outfile="$$ep_dir/concurrency-$${c}.txt"; \
		echo "===> $(EP) -c $$c $(DURATION)"; \
		$(HEY) -c $$c -z $(DURATION) $(if $(QPS),-q $(QPS),) $(HEADERS) "$(BASE)$(EP)" > "$$outfile" 2>&1 || true; \
	done

.PHONY: wait-healthy restart sweep-all

wait-healthy:
	@until curl -sf "$(BASE)/healthz" >/dev/null; do sleep 0.5; done

restart:
	docker compose restart backend >/dev/null
	$(MAKE) --no-print-directory wait-healthy

sweep-all:
	@for ep in $(ENDPOINTS); do \
		$(MAKE) --no-print-directory restart; \
		$(MAKE) --no-print-directory check-pool-hard || { echo "Pool dirty before $$ep"; exit 1; }; \
		$(MAKE) --no-print-directory sweep EP=$$ep; \
	done
	@echo "Logs in $(LOG_DIR)"

.PHONY: check-pool check-pool-hard
check-pool:
	@curl -sf "$(BASE)/api/v1/exp/pool/stats" | jq '.in_use, .checkouts, .checkins'

check-pool-hard:
	@stats=$$(curl -sf "$(BASE)/api/v1/exp/pool/stats"); \
	in_use=$$(echo $$stats | jq '.in_use'); \
	diff=$$(echo $$stats | jq '.checkouts - .checkins'); \
	if [ "$$in_use" != "0" ] || [ "$$diff" != "0" ]; then \
		echo "Pool not clean: in_use=$$in_use diff=$$diff"; exit 1; \
	fi

.PHONY: sweep-keepalive-off
sweep-keepalive-off:
	@ep_dir="$(LOG_DIR)/$(subst /,-,$(EP))"; \
	mkdir -p "$$ep_dir"; \
	for c in $(CONC); do \
		outfile="$$ep_dir/kaoff-concurrency-$${c}.txt"; \
		$(HEY) -disable-keepalive -c $$c -z $(DURATION) $(HEADERS) "$(BASE)$(EP)" > "$$outfile" 2>&1 || true; \
	done

PARSE_DIR ?= $(LOG_DIR)

.PHONY: parse
parse:
	@if [ ! -d "$(PARSE_DIR)" ]; then \
		echo "No logs found at $(PARSE_DIR). Set RUN=<name> if you recorded under a different run."; \
		exit 1; \
	fi
	uv run python scripts/hey_to_csv.py "$(PARSE_DIR)" "$(PARSE_DIR)/summary.json" "$(RUN)"
	@echo "Parsed run '$(RUN)' -> $(PARSE_DIR)/summary.json"

.PHONY: compare-di
compare-di:
	$(MAKE) --no-print-directory sweep RUN=$(RUN) EP=/api/v1/exp/di-sync/good
	$(MAKE) --no-print-directory sweep RUN=$(RUN) EP=/api/v1/exp/async/di
	$(MAKE) --no-print-directory parse RUN=$(RUN) PARSE_DIR=$(LOG_ROOT)/$(RUN)

.PHONY: compare-di-default compare-di-anyio200
compare-di-default:
	$(MAKE) --no-print-directory compose-up ANYIO_TOKENS=40
	$(MAKE) --no-print-directory wait-healthy
	$(MAKE) --no-print-directory compare-di RUN=compare-di-default

compare-di-anyio200:
	$(MAKE) --no-print-directory compose-up ANYIO_TOKENS=200
	$(MAKE) --no-print-directory wait-healthy
	$(MAKE) --no-print-directory compare-di RUN=compare-di-anyio200
