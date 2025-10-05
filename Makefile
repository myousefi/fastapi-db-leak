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
CONC ?= 5 25 50 100 250
QPS ?=
HEADERS := -H "Authorization: Bearer $(TOKEN)"

ENDPOINTS := \
	/api/v1/exp/inline-sync/filters \
	/api/v1/exp/di-sync/good \
	/api/v1/exp/mw-sync/filters \
	/api/v1/exp/async/di \
	/api/v1/exp/pool/stats \
	/api/v1/exp/di-sync/leak \
	/api/v1/exp/di-sync/nocache \
	/api/v1/exp/di-sync/manual-next \
	/api/v1/exp/mw-sync-leak/filters \
	/api/v1/exp/async/bridge \
	/api/v1/exp/async/loop-blocking \
	/api/v1/exp/longhold/2

LOG_DIR := logs/$(shell date +%Y%m%d-%H%M%S)
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
	mkdir -p $(LOG_DIR)
	@for c in $(CONC); do \
		outfile="$(LOG_DIR)/concurrency-$${c}-$(subst /,-,$(EP)).txt"; \
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
	mkdir -p $(LOG_DIR)
	@for c in $(CONC); do \
		outfile="$(LOG_DIR)/kaoff-concurrency-$${c}-$(subst /,-,$(EP)).txt"; \
		$(HEY) -disable-keepalive -c $$c -z $(DURATION) $(HEADERS) "$(BASE)$(EP)" > "$$outfile" 2>&1 || true; \
	done

PARSE_DIR ?= $(LOG_DIR)

.PHONY: parse
parse:
	python3 scripts/hey_to_csv.py "$(PARSE_DIR)" "$(PARSE_DIR)/summary.csv"
	@echo "Parsed -> $(PARSE_DIR)/summary.csv"
