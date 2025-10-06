# Convenience operations (POSIX env). PowerShell version: ops.ps1

PROJECT?=fullstack-ecosystem
PY?=python
PROMTOOL_VERSION?=2.52.0
SUMMARY_APP?=autogen.ultimate_enterprise_summary:UltimateEnterpriseSummary().app
SUMMARY_PORT?=8000

.PHONY: help up down restart logs prom-rules prom-rules-test promtool-install tldr seed-fleet seeder-dry-run ci-local build test platforms-up platforms-down alerts-sync alerts-validate mypy type-check type-baseline pre-commit-install pre-commit-run pre-commit-update pre-commit-install pre-commit-run pre-commit-update

	help:
	@echo 'Targets:'
	@echo '  up           - Start (docker compose up -d)' \
	      'and wait basic services'
	@echo '  summary-run  - Run summary service locally (uvicorn)'
	@echo '  summary-smoke - Run smoke auth script against local summary'
	@echo '  down         - Stop & remove containers'
	@echo '  restart      - Restart core observability services'
	@echo '  logs         - Tail gateway + summary'
	@echo '  prom-rules   - Validate Prometheus rules (requires promtool)'
	@echo '  prom-rules-test - Run promtool unit tests (docker/prometheus_rules.test.yml)'
	@echo '  promtool-install - Download promtool $(PROMTOOL_VERSION) to ./bin'
	@echo '  tldr         - Regenerate runbook TL;DR'
	@echo '  seed-fleet   - Run synthetic seeder once'
	@echo '  seeder-dry-run - Run synthetic seeder with SEED_DRY_RUN=1'
	@echo '  ci-local     - Run markdown lint, promtool checks/tests, pytest'
	@echo '  test         - Run pytest'
	@echo '  platforms-up   - Launch platform/domain services stack'
	@echo '  platforms-down - Tear down platform/domain services stack'
	@echo '  alerts-sync    - Sync alert taxonomy JSON with rules'
	@echo '  alerts-validate- Validate taxonomy schema'
	@echo '  mypy         - Run mypy type checking (selective strictness for metrics helpers)'
	@echo '  type-check   - Run mypy type checking with baseline (new comprehensive approach)'
	@echo '  type-baseline - Generate mypy baseline report (mypy-baseline.txt)'
	@echo '  pre-commit-install - Install pre-commit hooks'
	@echo '  pre-commit-run     - Run pre-commit on all files'
	@echo '  pre-commit-update  - Update pre-commit hook versions'
	@echo '  format       - Run code formatting (black + ruff format)'
	@echo '  lint         - Run code linting (ruff + flake8)'
	@echo '  quality      - Run both formatting and linting'
	@echo '  benchmark-quantiles - Run quantile approximation benchmark (cache vs disabled)'
	@echo '  aggregate-benchmarks - Aggregate quantile benchmark JSON artifacts into summary outputs'
	@echo '  lint-docs    - Run markdownlint-cli2 on Markdown files (local convenience)'
	@echo '  mypy-strict  - Run mypy in strict mode on core dashboard & config modules'
	@echo '  pre-commit-install - Install pre-commit hooks'
	@echo '  pre-commit-run     - Run pre-commit on all files'
	@echo '  pre-commit-update  - Update pre-commit hook versions'

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart prometheus alertmanager grafana gateway summary || true

logs:
	docker compose logs -f gateway summary

summary-run:
	LOG_LEVEL=INFO JSON_LOGGING=true uvicorn $(SUMMARY_APP) --port $(SUMMARY_PORT)

summary-smoke:
	python scripts/smoke_auth.py --base http://localhost:$(SUMMARY_PORT) --user admin --password changeme || true

prom-rules:
	promtool check rules docker/prometheus_rules.yml

prom-rules-test:
	@if [ -f docker/prometheus_rules.test.yml ]; then promtool test rules docker/prometheus_rules.test.yml; else echo 'No promtool test file found'; fi

promtool-install:
	@mkdir -p bin
	@if [ ! -f bin/promtool ]; then \
	  echo 'Downloading promtool $(PROMTOOL_VERSION)...'; \
	  unameOut=$$(uname -s 2>/dev/null || echo Unknown); \
	  case "$$unameOut" in \
	    Linux*)   os=linux ;; \
	    Darwin*)  os=darwin ;; \
	    *)        os=linux ;; \
	  esac; \
	  arch=$$(uname -m 2>/dev/null || echo amd64); \
	  if [ "$$arch" = "x86_64" ]; then arch=amd64; fi; \
	  if [ "$$arch" = "arm64" ] || [ "$$arch" = "aarch64" ]; then arch=arm64; fi; \
	  url="https://github.com/prometheus/prometheus/releases/download/v$(PROMTOOL_VERSION)/prometheus-$(PROMTOOL_VERSION).$$os-$$arch.tar.gz"; \
	  echo "Fetching $$url"; \
	  curl -sSL $$url -o /tmp/prometheus.tgz && tar -xzf /tmp/prometheus.tgz -C /tmp && \
	    cp /tmp/prometheus-$(PROMTOOL_VERSION).$$os-$$arch/promtool bin/promtool && \
	    chmod +x bin/promtool && echo 'promtool installed to bin/promtool'; \
	else \
	  echo 'promtool already present'; \
	fi

tldr:
	$(PY) scripts/generate_runbook_tldr.py

seed-fleet:
	$(PY) scripts/synthetic_seed.py || echo 'Seeder script missing or exited'

seeder-dry-run:
	SEED_DRY_RUN=1 $(PY) scripts/synthetic_seed.py || echo 'Seeder script missing or exited'

test:
	pytest -q || true

ci-local:
	@if command -v markdownlint >/dev/null 2>&1; then markdownlint . || true; else echo 'markdownlint not installed (CI uses action).'; fi
	@if command -v promtool >/dev/null 2>&1; then promtool check rules docker/prometheus_rules.yml; else echo 'promtool not installed'; fi
	@if command -v promtool >/dev/null 2>&1 && [ -f docker/prometheus_rules.test.yml ]; then promtool test rules docker/prometheus_rules.test.yml; fi
	@echo 'Running mypy selective strictness...'; if command -v mypy >/dev/null 2>&1; then mypy tests/utils/metrics.py || true; else echo 'mypy not installed'; fi
	pytest -q || true

platforms-up:
	docker compose -f docker-compose.platforms.yml up -d --build

platforms-down:
	docker compose -f docker-compose.platforms.yml down -v

alerts-sync:
	$(PY) scripts/sync_alert_taxonomy.py --rules docker/prometheus_rules.yml --taxonomy alerts_taxonomy.json --scaffold

alerts-validate:
	$(PY) scripts/validate_taxonomy_schema.py

# Type checking (selective strictness configured in mypy.ini)
mypy:
	@echo 'Type checking metrics helpers and any additional annotated utils...'
	mypy tests/utils/metrics.py tests/utils/*.py scripts/benchmark_metrics_quantiles.py scripts/aggregate_quantile_benchmarks.py scripts/load_env.py
	mypy scripts/prune_benchmark_artifacts.py

# New comprehensive type checking with baseline approach
type-check:
	$(PY) scripts/type_check.py

type-baseline:
	$(PY) scripts/type_check.py --baseline

.PHONY: mypy-strict
mypy-strict:
	@echo 'Running mypy strict mode on selected modules...'
	@if command -v mypy >/dev/null 2>&1; then \
	  mypy --strict unified_master_dashboard.py config.py dashboard/__init__.py || true; \
	else \
	  echo 'mypy not installed'; \
	fi

.PHONY: mypy-strict-ci
mypy-strict-ci:
	@echo 'Running mypy strict CI (failing on any type errors)...'
	@if command -v mypy >/dev/null 2>&1; then \
	  mypy --strict unified_master_dashboard.py config.py dashboard/__init__.py; \
	else \
	  echo 'mypy not installed' && exit 1; \
	fi

benchmark-quantiles:
	@if [ -n "$$BENCH_OUT" ]; then \
	  echo "Writing benchmark JSON to $$BENCH_OUT"; \
	  $(PY) scripts/benchmark_metrics_quantiles.py --json-out $$BENCH_OUT; \
	else \
	  $(PY) scripts/benchmark_metrics_quantiles.py; \
	fi

aggregate-benchmarks:
	@if [ -z "$$INPUT_GLOB" ]; then echo 'Please set INPUT_GLOB (e.g., artifacts/quantile_bench_*.json)'; exit 1; fi; \
	CMD="$(PY) scripts/aggregate_quantile_benchmarks.py --input-glob $$INPUT_GLOB"; \
	if [ -n "$$JSON_OUT" ]; then CMD="$$CMD --json-out $$JSON_OUT"; fi; \
	if [ -n "$$MD_OUT" ]; then CMD="$$CMD --markdown-out $$MD_OUT"; fi; \
	if [ -n "$$MIN_SPEEDUP" ]; then CMD="$$CMD --min-speedup-warn $$MIN_SPEEDUP"; fi; \
	echo "Running: $$CMD"; \
	sh -c "$$CMD"

lint-docs:
	@if command -v markdownlint-cli2 >/dev/null 2>&1; then \
	  echo 'Running markdownlint-cli2...'; \
	  markdownlint-cli2 "**/*.md" "#node_modules"; \
	else \
	  echo 'markdownlint-cli2 not installed; install with: npm install -g markdownlint-cli2'; \
	fi

# Ensure PYTHONPATH (helpful for CI): verifies sitecustomize loads and tests.utils import works
.PHONY: ensure-pythonpath
ensure-pythonpath:
	@echo "PYTHONPATH=$$PYTHONPATH"
	@$(PY) -c "import sys; import site; print('sys.path[0:3]=', sys.path[:3]); import sitecustomize; print('sitecustomize loaded OK')"
	@$(PY) -c "from tests.utils.metrics import assert_metric_present; print('metrics helper import OK')"

# --- Extended pytest profiles ---
.PHONY: test-fast test-slow test-integration test-all test-scripts

test-fast:
	python -m pytest

test-slow:
	python -m pytest -m slow

test-integration:
	python -m pytest -m integration

test-all:
	python -m pytest -m "slow or integration or not slow"

test-scripts:
	python -m pytest tests/scripts -q

# --- Governance App Targets ---
GOV_PORT?=8081
GOV_APP=governance_app.app:app
GOV_REQ=governance_app/requirements.txt

.PHONY: gov-venv gov-install gov-run gov-sim gov-docker-build gov-docker-run

gov-venv:
	$(PY) -m venv .gov-venv

gov-install: gov-venv
	./.gov-venv/Scripts/python -m pip install -r $(GOV_REQ)

gov-run:
	set WEBHOOK_SECRET=devsecret && set PYTHONPATH=. && ./.gov-venv/Scripts/python -m uvicorn $(GOV_APP) --port $(GOV_PORT) --reload

gov-sim:
	@if not exist .github/workflows mkdir .github/workflows
	@if not exist .github/workflows/example.yml \
	 ( echo name: Example> .github/workflows/example.yml & \
	   echo on: push>> .github/workflows/example.yml & \
	   echo jobs:>> .github/workflows/example.yml & \
	   echo   test:>> .github/workflows/example.yml & \
	   echo     runs-on: ubuntu-latest>> .github/workflows/example.yml & \
	   echo     steps:>> .github/workflows/example.yml & \
	   echo       - uses: actions/checkout@v4>> .github/workflows/example.yml & \
	   echo       - uses: someorg/someaction@v1>> .github/workflows/example.yml )
	set GOV_APP_PORT=$(GOV_PORT) && ./.gov-venv/Scripts/python governance_app/sample_push_event.py

gov-docker-build:
	docker build -f governance_app/Dockerfile -t governance-app:latest .

gov-docker-run:
	docker run -e WEBHOOK_SECRET=devsecret -p $(GOV_PORT):8081 governance-app:latest

# --- Code Quality Targets ---
.PHONY: format lint quality

format:
	$(PY) scripts/format.py

lint:
	$(PY) scripts/lint.py

quality:
	$(PY) scripts/quality.py

# Pre-commit hooks management
pre-commit-install:
	pre-commit install --install-hooks
	pre-commit install --hook-type pre-push

pre-commit-run:
	pre-commit run --all-files

pre-commit-update:
	pre-commit autoupdate
