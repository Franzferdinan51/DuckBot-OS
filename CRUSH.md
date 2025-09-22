## DuckBot Enhanced Development Guide

This file provides essential commands and guidelines for agentic coding in the DuckBot codebase.

### Development Commands

**Dependencies:**
- Install: `python -m pip install -r docs/requirements.txt`
- uv sync: `uv sync` (uses pyproject.toml/uv.lock)

**Build/Run:**
- Local: `python start_local_ecosystem.py`
- Full: `python start_ecosystem.py`
- AI Manager: `python ai_ecosystem_manager.py`
- WebUI: `python -m duckbot.enhanced_webui --host 127.0.0.1 --port 8787`

**Testing:**
- Full suite: `python tests/unified_test_suite.py`
- Category: `python tests/unified_test_suite.py --category core_system` (categories: core_system, integrations, webui, hardware, action_reasoning, enhanced_features, external_deps, configuration)
- Single file: `python -m pytest tests/test_file.py`
- Single function: `python -m pytest tests/test_file.py::test_function_name -v`
- Integration: `python tests/run_integration_tests.py`

**Linting & Quality:**
- Lint: `ruff check duckbot/`
- Fix lint: `ruff check --fix duckbot/`
- Format: `black duckbot/ --line-length 88`
- Imports: `isort duckbot/`
- Type check: `mypy duckbot/ --config-file mypy.ini`
- All: `isort duckbot/ && black duckbot/ && ruff check --fix duckbot/ && mypy duckbot/`

### Code Style Guidelines

- **Formatting:** Black (line length 88). No trailing whitespace.
- **Imports:** Group: standard, third-party, local. Absolute imports. Sort with isort.
- **Naming:** PascalCase (classes), snake_case (functions/vars), UPPER_SNAKE_CASE (constants).
- **Typing:** Type hints everywhere (params, returns, vars). Use typing or built-ins.
- **Error Handling:** Log via `duckbot/core/logging_setup.py`. Raise specific exceptions. Try-except for async.
- **Concurrency:** Async/await for I/O; asyncio.gather for parallels.
- **Modularity:** Core: `duckbot/core/`; Integrations: `duckbot/integrations/`. Single responsibility.
- **Documentation:** Google-style docstrings for public APIs. Minimal inline comments.
- **Security:** No logging secrets. Validate inputs (Pydantic). PEP 8/484 compliant.

### Notes
- No Cursor/Copilot rules in `.cursor/` or `.github/copilot-instructions.md`.
- Follow `CLAUDE.md` for architecture.
- Test local-only mode for privacy.
