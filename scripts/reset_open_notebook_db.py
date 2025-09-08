"""
Reset Open Notebook database in SurrealDB and local state.

Actions:
- Connects to SurrealDB using env vars (from open-notebook/.env if present).
- Tries to REMOVE DATABASE <db> in namespace <ns>.
- If that fails, falls back to dropping all tables and clearing migrations.
- Removes LangGraph checkpoint sqlite to clear local thread state.

Env vars used (typical defaults if running locally):
- SURREAL_URL: ws://localhost:8000/rpc
- SURREAL_USER: root
- SURREAL_PASSWORD: root
- SURREAL_NAMESPACE: open_notebook
- SURREAL_DATABASE: staging
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv


def _ensure_env_defaults() -> None:
    # Provide sane local defaults if not explicitly set
    os.environ.setdefault("SURREAL_URL", "ws://localhost:8000/rpc")
    os.environ.setdefault("SURREAL_USER", "root")
    os.environ.setdefault("SURREAL_PASSWORD", os.environ.get("SURREAL_PASS", "root"))
    os.environ.setdefault("SURREAL_NAMESPACE", "open_notebook")
    os.environ.setdefault("SURREAL_DATABASE", "staging")


async def _reset_db() -> int:
    # Lazy imports to ensure venv resolves packages
    from open_notebook.database.repository import db_connection  # type: ignore

    ns = os.environ.get("SURREAL_NAMESPACE")
    db = os.environ.get("SURREAL_DATABASE")
    if not ns or not db:
        print("error: missing SURREAL_NAMESPACE or SURREAL_DATABASE in environment")
        return 2

    # Try hard reset: remove database from namespace
    try:
        async with db_connection() as conn:
            # Switch to namespace-only context before removing database
            await conn.query(f"USE NS {ns}; REMOVE DATABASE {db};")
        print(f"removed_database: ns={ns} db={db}")
        return 0
    except Exception as e:
        print(f"warn: remove database failed: {e}")

    # Fallback: drop all tables in current DB and clear migrations
    try:
        async with db_connection() as conn:
            info = await conn.query("INFO FOR DB;")
            # Surreal returns a list of statements; take first result payload
            dbinfo: Dict[str, Any] = (info[0] if isinstance(info, list) else info) or {}
            tb = (dbinfo.get("result") or {}).get("tb") or {}
            tables = list(tb.keys()) if isinstance(tb, dict) else []

            # Drop user tables first
            for t in tables:
                try:
                    await conn.query(f"REMOVE TABLE {t};")
                    print(f"dropped_table: {t}")
                except Exception as te:
                    print(f"warn: failed drop {t}: {te}")

            # Ensure migrations table is cleared
            try:
                await conn.query("DELETE _sbl_migrations;")
            except Exception:
                pass
            try:
                await conn.query("REMOVE TABLE _sbl_migrations;")
            except Exception:
                pass

        print("database_cleared: tables dropped and migrations reset")
        return 0
    except Exception as e:
        print(f"error: failed to clear database: {e}")
        return 1


def _remove_local_checkpoints() -> None:
    # Clear LangGraph sqlite checkpoint for a fully fresh start
    ckpt = Path("open-notebook/data/sqlite-db/checkpoints.sqlite")
    try:
        if ckpt.exists():
            ckpt.unlink()
            print(f"removed_checkpoint: {ckpt}")
    except Exception as e:
        print(f"warn: failed removing checkpoint {ckpt}: {e}")


def main() -> int:
    # Load .env from project
    load_dotenv(dotenv_path=Path("open-notebook/.env"), override=False)
    _ensure_env_defaults()
    rc = asyncio.run(_reset_db())
    _remove_local_checkpoints()
    return rc


if __name__ == "__main__":
    raise SystemExit(main())

