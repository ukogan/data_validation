# Repository Guidelines

## Project Structure & Module Organization
- `main.py` exposes the FastAPI service, pulling analytics logic from `src` and serving data to the dashboard clients.
- Domain code lives in `src`: `src/data` handles ingestion/config, `src/analysis` produces occupancy metrics, and `src/presentation` formats reports; keep new modules in the nearest matching package.
- Static assets and UI scaffolding live alongside the server: `timeline_viewer.html`, `public/`, `mockups/`, and `screenshots/` support demo flows, while raw CSV fixtures stay in the repository root.

## Build, Test, and Development Commands
- `python -m venv venv && source venv/bin/activate` and `pip install -r requirements.txt` prepare the FastAPI environment.
- `uvicorn main:app --reload --port 8000` hot-reloads analytics APIs; hit `http://localhost:8000/docs` to sanity check endpoints.
- `npm install` followed by `npm run start` serves the static dashboard via Express on port 3000, proxying assets from `public/`.
- Use `python generate_mock_data.py --days 5` or the existing `SCH-1_*.csv` files to simulate incoming telemetry before testing.

## Coding Style & Naming Conventions
- Follow PEP 8: 4-space indentation, snake_case modules/functions, type-annotate public interfaces, and keep docstrings descriptive.
- Keep JS consistent with `server.js`: `const`/`let` over `var`, promise-based fetch helpers, and 2-space indents when touching client-facing scripts.
- Place configuration constants in `src/data/config.py` and mirror existing `SENSOR_ZONE_MAP` naming when adding new zones.

## Testing Guidelines
- Tests rely on pytest and Playwright; ensure the FastAPI app (port 8000) and Express server (port 3000) are running first.
- Run `python -m pytest -k dashboard` to execute UI regression scripts; provide `--headed` or `--browser chromium` flags as needed for debugging.
- Store generated screenshots or JSON artifacts under `screenshots/` and keep large data exports out of version control.

## Commit & Pull Request Guidelines
- Match the Conventional Commit style already in history (`feat(scope): summary`, `fix(scope): ...`); keep scope names aligned with folders (`dashboard`, `ui`, `analysis`).
- PRs should include: purpose summary, affected datasets or endpoints, testing evidence (command logs or screenshots), and links to tracking issues or dashboards.
- Highlight any new environment variables (`GOOGLE_CLIENT_ID`, FastAPI ports) and update `.env.example` or docs when configuration changes.
