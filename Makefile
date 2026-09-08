.PHONY: backend-install backend-dev backend-tests lint frontend-install frontend-dev frontend-build test

backend-install:
	cd backend && python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt

backend-dev:
	cd backend && .venv/bin/uvicorn app.main:app --reload

backend-tests:
	cd backend && .venv/bin/python -m pytest -q

frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

test:
	cd backend && .venv/bin/python -m pytest -q

lint:
	cd backend && .venv/bin/ruff check app