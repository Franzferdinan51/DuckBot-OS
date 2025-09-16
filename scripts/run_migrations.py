from __future__ import annotations

from dotenv import load_dotenv
from pathlib import Path
import os

from open_notebook.database.migrate import MigrationManager  # type: ignore


def main() -> int:
    # Ensure we run from the open-notebook folder so migration file paths resolve
    repo_root = Path(__file__).resolve().parent.parent
    on_dir = repo_root / "open-notebook"
    os.chdir(on_dir)
    load_dotenv(on_dir / ".env")
    mm = MigrationManager()
    if mm.needs_migration:
        mm.run_migration_up()
        print("migrations_applied")
    else:
        print("no_migration_needed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
