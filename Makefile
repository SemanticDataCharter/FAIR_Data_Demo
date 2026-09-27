# FAIR Data Demo: three federal health studies on one component library, clone-and-run.
#
# Requirements: Docker (or Podman) with the compose plugin, ~10GB free RAM,
# Python 3.12 on the host (for data generation only), and the federal source
# files in source_data/ (see source_data/README.md; NHANES and BRFSS converted
# once with scripts/convert_xpt_to_csv.py).
#
# Typical first run:
#   make demo      # start the stack, generate the sampled dataset, load it
# then open http://localhost:18100/console/

COMPOSE := docker compose -f app/sdc4/docker-compose.yml
WEB_URL  := http://localhost:18100

.PHONY: help up down demo demo-full generate generate-full load wait-web clean

help:
	@echo "FAIR Data Demo quickstart:"
	@echo "  make demo        Start the stack + generate + load the seeded samples: all of NHANES,"
	@echo "                   5,000 BRFSS respondents, 1,000 CMS beneficiaries with all their claims"
	@echo "                   (84,352 records; about 107 minutes to load). The default."
	@echo "  make demo-full   Same, but every row of every source file (about 7 million records;"
	@echo "                   days to load at the measured rate)."
	@echo "  make up          Start the stack only."
	@echo "  make down        Stop the stack."
	@echo "  make clean       Stop the stack and remove generated import data."
	@echo ""
	@echo "After 'make demo':"
	@echo "  $(WEB_URL)/console/   the record console (start here)"
	@echo "  $(WEB_URL)/demo/      dashboard, the six-beat walk-through, SPARQL explorer"

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

# Wait until the web app answers before loading (first run migrates + inits GraphDB).
wait-web:
	@echo "Waiting for the web app at $(WEB_URL) (first run can take 1-2 min)..."
	@until curl -sf $(WEB_URL)/ >/dev/null 2>&1; do sleep 3; done
	@echo "Web app is up."

# Generation runs on the host (Python 3.12 + lxml); reads source_data/, writes app/sdc4/import_data/.
generate:
	@python3 -m pip install -q -r datagen/requirements.txt
	cd datagen && python3 generate_all.py

generate-full:
	@python3 -m pip install -q -r datagen/requirements.txt
	cd datagen && FAIR_FULL=1 python3 generate_all.py

# Loading runs in the web container (validates each instance, writes Postgres + GraphDB).
load: wait-web
	$(COMPOSE) exec -T web python manage.py load_all_data --clear --batch 200

demo: up generate load
	@echo ""
	@echo "Demo ready. Expect 84,352 records across 7 models, 84,352 named graphs."
	@echo ""
	@echo "  $(WEB_URL)/console/   the record console (start here)"
	@echo "  $(WEB_URL)/demo/      dashboard, the six-beat walk-through, SPARQL explorer"

demo-full: up generate-full load
	@echo ""
	@echo "Full dataset ready."
	@echo ""
	@echo "  $(WEB_URL)/console/   the record console (start here)"
	@echo "  $(WEB_URL)/demo/      dashboard, the six-beat walk-through, SPARQL explorer"

clean:
	$(COMPOSE) down
	@find app/sdc4/import_data -mindepth 1 -maxdepth 1 -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "Stack stopped and generated import data removed."

# --- release plumbing -------------------------------------------------------
VERSION := $(shell tr -d '[:space:]' < app/sdc4/VERSION)

version:            ## Print the version (app/sdc4/VERSION is the single source)
	@echo $(VERSION)

test:               ## Run the unit tests inside the web image (no database or triple store needed)
	$(COMPOSE) run --rm --no-deps -e DATABASE_URL=sqlite:////tmp/test.sqlite3 web python manage.py test demo console

pull:               ## Pull the published web image for this version instead of building it
	FAIR_IMAGE_TAG=$(VERSION) $(COMPOSE) pull web

release-check:      ## What the release workflow checks: VERSION is tagged, tag is on main
	@git tag -l "v$(VERSION)" | grep -q . && echo "v$(VERSION) is tagged" || echo "v$(VERSION) is not tagged yet: git tag -a v$(VERSION) -m 'FAIR Data Demo $(VERSION)' && git push origin v$(VERSION)"

