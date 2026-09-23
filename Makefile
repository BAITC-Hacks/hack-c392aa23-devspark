.PHONY: up dev test

up:
	docker compose up --build

dev:
	PYTHONPATH=backend uvicorn app.main:app --reload --port 8000

test:
	cd backend && pytest -q
