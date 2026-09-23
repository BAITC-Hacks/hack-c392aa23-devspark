.PHONY: up dev test eval fixtures og

up:
	docker compose up --build

dev:
	PYTHONPATH=backend uvicorn app.main:app --reload --port 8000

test:
	cd backend && pytest -q

# Trap-profile evaluation: naive baseline vs rules vs AI (AI column needs LLM_API_KEY)
eval:
	python eval/run_eval.py

# Regenerate the landing page data from the real engine/API (uses .env for the AI layer)
fixtures:
	python backend/scripts/export_landing_fixtures.py

# Re-render the social-share image from the fixtures (needs Pillow)
og:
	python3 backend/scripts/render_og_image.py
