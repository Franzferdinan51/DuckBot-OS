#!/usr/bin/env python3
"""
Validate key DuckBot launcher options by starting servers briefly and checking health.
This avoids long-running processes and exits cleanly.
"""
from __future__ import annotations

import os
import sys
import time
import subprocess
import contextlib
from pathlib import Path
import socket
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def wait_http(url: str, timeout: float = 10.0) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                return resp.status < 500
        except Exception:
            time.sleep(0.3)
    return False


def start_and_check(cmd: list[str], health_url: str, wait: float = 12.0, env: dict | None = None) -> bool:
    proc = subprocess.Popen(cmd, cwd=str(ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
    try:
        ok = wait_http(health_url, timeout=wait)
        return ok
    finally:
        with contextlib.suppress(Exception):
            proc.terminate()
        with contextlib.suppress(Exception):
            proc.kill()


def main() -> int:
    tests = []

    # Enhanced WebUI (Option 2) on a test port
    env = os.environ.copy(); env["DUCKBOT_FAST_IMPORT"] = "1"
    tests.append((
        [sys.executable, "-m", "duckbot.enhanced_webui", "--host", "127.0.0.1", "--port", "8791"],
        "http://127.0.0.1:8791/healthz",
        "Enhanced WebUI"
    ))

    # Monitoring Dashboard (Option 3)
    tests.append((
        [sys.executable, "-m", "duckbot.monitoring_dashboard"],
        "http://127.0.0.1:8789/healthz",
        "Monitoring Dashboard"
    ))

    # Classic Enhanced (Option 7)
    tests.append((
        [sys.executable, "-m", "duckbot.classic_enhanced"],
        "http://127.0.0.1:8792/healthz",
        "Classic Enhanced"
    ))

    # Local Privacy (Option 8)
    tests.append((
        [sys.executable, "-m", "duckbot.local_privacy_mode"],
        "http://127.0.0.1:8793/healthz",
        "Local Privacy"
    ))

    # Hybrid Cloud (Option 9)
    tests.append((
        [sys.executable, "-m", "duckbot.hybrid_cloud_mode"],
        "http://127.0.0.1:8794/healthz",
        "Hybrid Cloud"
    ))

    all_pass = True
    for idx, (cmd, url, name) in enumerate(tests):
        print(f"[CHECK] Starting {name}...")
        use_env = env if idx == 0 else None
        ok = start_and_check(cmd, url, env=use_env)
        print(f"  {name}: {'PASS' if ok else 'FAIL'} ({url})")
        all_pass &= ok

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
