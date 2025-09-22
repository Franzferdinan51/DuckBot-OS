#!/usr/bin/env python3
"""
DuckBot Monitoring Dashboard (minimal)
Provides a lightweight FastAPI app with basic health and system metrics.
Used by START_ENHANCED_DUCKBOT.bat option 3.
"""
from __future__ import annotations

import os
from typing import Dict, Any
from datetime import datetime

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(title="DuckBot Monitoring Dashboard", version="1.0")


@app.get("/healthz")
def healthz() -> Dict[str, Any]:
    return {"ok": True, "ts": datetime.utcnow().isoformat() + "Z"}


@app.get("/status")
def status() -> Dict[str, Any]:
    try:
        import psutil  # type: ignore
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory().percent
    except Exception:
        cpu = 0.0
        mem = 0.0
    return {
        "time": datetime.utcnow().isoformat() + "Z",
        "cpu_percent": cpu,
        "mem_percent": mem,
        "note": "minimal monitoring service",
    }


def main() -> None:
    host = os.getenv("DUCKBOT_MONITOR_HOST", "127.0.0.1")
    port = int(os.getenv("DUCKBOT_MONITOR_PORT", "8789"))
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()

