# CRUSH.md - Development Guidelines for AI Coding Agents

## Build/Run Commands
```bash
# Main project (DuckBot)
python start_ai_ecosystem.py          # Start complete ecosystem
python -m duckbot.webui               # Enhanced WebUI
START_ENHANCED_DUCKBOT.bat            # Main launcher (Windows)

# Open Notebook subproject
cd open-notebook
make run                              # Run UI only
make start-all                        # Start complete system (DB + API + Worker + UI)
make api                              # Start API only
make worker                           # Start background worker
```

## Test Commands
```bash
# Open Notebook testing (primary testing setup)
cd open-notebook
make lint                             # Type checking with mypy
make ruff                             # Code linting
uv run python -m mypy .               # Direct mypy execution
ruff check . --fix                    # Direct ruff execution
```

## Lint/Format Commands
```bash
# Code formatting and linting (Open Notebook)
cd open-notebook
make ruff                             # Run ruff linter and auto-fix
ruff check . --fix                    # Direct ruff execution
uv run python -m mypy .               # Type checking
make lint                             # Mypy type checking via Makefile

# Cleanup
make clean-cache                      # Remove cache directories
```

## Code Style Guidelines

### Python Conventions
- Follow PEP 8 style guide
- Use type hints extensively (enforced by mypy)
- Line length: 88 characters
- Use `snake_case` for variables/functions, `PascalCase` for classes
- Write docstrings for all functions, classes, and modules

### Imports
- Use absolute imports when possible
- Group imports in standard order: standard library, third-party, local
- Use isort with black profile (line_length=88)

### Linting/Formatting Tools
- Ruff for linting (E, F, I error codes)
- Mypy for type checking
- Black-compatible formatting enforced via Ruff

### Error Handling
- Use specific exception types rather than generic exceptions
- Log errors appropriately with context
- Follow existing error handling patterns in the codebase

### Project Structure
- Modular design with clear separation of concerns
- Domain-driven design in open-notebook subsystem
- API routes organized by resource type