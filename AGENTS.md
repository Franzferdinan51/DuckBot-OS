# Repository Guidelines

## Project Structure & Module Organization
- Root: `SETUP_AND_START.bat` (guided setup/run), `.env` for secrets.
- Source: Python package under `duckbot/` (e.g., `webui`, agents, utilities). Run with `py -3 -m duckbot.webui`.
- Scripts: helper scripts in `scripts/` (`.bat`, `.ps1`).
- Assets & logs: UI assets in `assets/`; runtime logs in `logs/`.
- Tests: `tests/` with `test_*.py` files.

## Build, Test, and Development Commands
- Install deps: `py -3 -m pip install -r requirements.txt` (use a venv).
- Launch setup menu: run `SETUP_AND_START.bat` from repo root.
- Start WebUI: `py -3 -m duckbot.webui` (defaults to `http://localhost:8787/`). Override port (Windows): `set DUCKBOT_WEBUI_PORT=8899`.
- Run tests: `pytest -q` or subset with `pytest -k <pattern>`.

## Coding Style & Naming Conventions
- Python: PEP 8; 4-space indentation; include type hints.
- Naming: `snake_case` for functions/vars, `PascalCase` for classes; files `lower_snake_case.py`.
- Formatters/Lint: run `black .`, `isort .`, and `ruff .` before pushing.

## Testing Guidelines
- Framework: `pytest`; place tests in `tests/` as `test_*.py`.
- Keep tests fast and isolated; mock network/external CLIs; use deterministic seeds/fixtures.
- Aim for meaningful coverage of changed code; prefer unit tests close to the implementation.

## Commit & Pull Request Guidelines
- Commits: small, focused; use Conventional Commits (e.g., `feat:`, `fix:`, `docs:`, `chore:`).
- PRs: link issues; include repro steps, root cause, minimal fix, and before/after logs or screenshots.
- Don’t remove features/files; maintain a brief Test Journal (before → root cause → fix → after).

## Security & Configuration Tips
- Use a virtual environment; keep secrets in `.env` or environment variables.
- Models: set `OPENROUTER_API_KEY` (optional `OPENROUTER_BASE_URL`). Routing via `AI_ROUTING_MODE=cloud_first|local_first`, `AI_MODEL_MAIN_BRAIN`, optional `LM_STUDIO_MODEL`.
- WebUI auth: local `localhost/127.0.0.1` bypass by default; visit `/token` for a helper payload; toggle with `DUCKBOT_WEBUI_LOCAL_BYPASS=0|1`.
- Resolve port conflicts on `8787`; override with `DUCKBOT_WEBUI_PORT`.
- Windows scripting: quote paths; prefer `pushd "%~dp0"` … `popd`; on failure use `if errorlevel 1 exit /b %errorlevel%`.

