from __future__ import annotations

import os
import re
import sys
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED


def should_exclude(path: Path) -> bool:
    exclude_dirs = {
        '.git', '.venv', 'env', 'logs', '__pycache__',
        '.pytest_cache', '.mypy_cache', 'node_modules'
    }
    exclude_files = {'.DS_Store'}
    exclude_exts = {'.pyc', '.pyo', '.log'}

    parts = set(p.name for p in path.parents)
    if parts & exclude_dirs:
        return True
    if path.name in exclude_files:
        return True
    if path.suffix in exclude_exts:
        return True
    return False


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    ts = datetime.now().strftime('%Y%m%d-%H%M')
    zip_name = f'DuckBotComplete-{ts}.zip'
    zip_path = repo_root / zip_name

    # Collect files
    files: list[Path] = []
    for p in repo_root.rglob('*'):
        if p.is_file():
            if p == zip_path:
                continue
            if should_exclude(p):
                continue
            files.append(p)

    if not files:
        print('No files to archive.', file=sys.stderr)
        return 1

    with ZipFile(zip_path, 'w', ZIP_DEFLATED) as zf:
        for f in files:
            zf.write(f, f.relative_to(repo_root))

    print(f'Created {zip_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

