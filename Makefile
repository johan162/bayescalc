PYTHON=.venv/bin/python

.PHONY: test test-pty compile regen-readme inject-readme test-slow test-sample test-all api-ref build

# Default Python interpreter to use for targets (use virtualenv if present)
PYTHON ?= .venv/bin/python

test-all: test-slow compile

# Run the fast test-suite (PTY tests are skipped by default unless enabled with --run-pty)
test:
	$(PYTHON) -m pytest -q

test-slow:
	$(PYTHON) -m pytest -q --run-pty --sample-test

# Run the full test-suite including PTY-based interactive tests
test-pty:
	$(PYTHON) -m pytest -q --run-pty

test-sample:
	$(PYTHON) -m pytest -q --sample-test

compile:
	# byte-compile all python files for a quick "compilation" speed check
	$(PYTHON) -m compileall -q .

regen-readme:
	# regenerate README CLI help section from code
	$(PYTHON) scripts/generate_readme_help.py > README_CLI.md


.PHONY: inject-readme
inject-readme: regen-readme
	# Inject generated CLI help into README.md between sentinel markers (prompt for confirmation)
	$(PYTHON) scripts/generate_readme_help.py --inject README.md --confirm

api-ref:
	# Generate / update API reference table in ARCHITECTURE.md
	$(PYTHON) scripts/generate_api_reference.py --file ARCHITECTURE.md

build:
	$(PYTHON) -m build

seq-demo: export PYTHONPATH := $(CURDIR)
seq-demo:
	$(PYTHON) scripts/sequential_demo.py

