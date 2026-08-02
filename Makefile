PYTHON ?= .venv/bin/python
NPM ?= npm

.PHONY: bootstrap ocr build-bank dev test build clean

bootstrap:
	python3 -m venv .venv
	.venv/bin/python -m pip install -r requirements.txt
	$(NPM) install

ocr:
	$(PYTHON) scripts/ocr_sources.py

build-bank:
	$(PYTHON) scripts/ocr_sources.py
	$(PYTHON) scripts/build_bank.py
	$(PYTHON) scripts/validate_bank.py

dev: build-bank
	$(NPM) run dev

test: build-bank
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py'
	$(NPM) run test

build: build-bank
	$(NPM) run build

clean:
	rm -rf dist coverage tmp/pdfs
