# Auto-discover tracks so `make new-track NAME=…` is picked up by
# install / update / weekly without a manual edit. Override with
# `make TRACKS="iam security" update` for ad-hoc runs.
TRACKS ?= $(notdir $(patsubst %/,%,$(wildcard tracks/*/)))

.PHONY: install update weekly new-track new-deep-dive test lint format audit dev-install

install:
	@for t in $(TRACKS); do echo "=== install: $$t ==="; $(MAKE) -C tracks/$$t install || exit $$?; done

update:
	@for t in $(TRACKS); do echo "=== update: $$t ==="; $(MAKE) -C tracks/$$t update || exit $$?; done

weekly:
	@for t in $(TRACKS); do echo "=== weekly: $$t ==="; $(MAKE) -C tracks/$$t weekly || exit $$?; done

new-track:
	@test -n "$(NAME)" || (echo "NAME=<track-name> required" >&2; exit 1)
	bash scripts/new-track.sh "$(NAME)"

new-deep-dive:
	@test -n "$(TRACK)" || (echo "TRACK=<track> required" >&2; exit 1)
	@test -n "$(TOPIC)" || (echo "TOPIC=<topic> required" >&2; exit 1)
	bash scripts/new-deep-dive.sh "$(TRACK)" "$(TOPIC)"

dev-install:
	pip install -r requirements.txt -r requirements-dev.txt

test:
	pytest --cov=awsdd --cov-report=term

lint:
	ruff check .

format:
	ruff format .

audit:
	pip-audit -r requirements.txt -r requirements-dev.txt
	cd web && npm audit --omit=dev --audit-level=high
