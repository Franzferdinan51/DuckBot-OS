#!/usr/bin/env python3
"""
DuckBot Hybrid Cloud Mode (stub)
Starts a simple FastAPI app indicating hybrid routing.
"""
from __future__ import annotations

import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(title="DuckBot Hybrid Cloud Mode", version="1.0")


@app.get("/healthz")
def health() -> JSONResponse:
    return JSONResponse({"ok": True, "mode": "hybrid_cloud", "routing": "hybrid"})


def main() -> None:
    host = os.getenv("DUCKBOT_HYBRID_HOST", "127.0.0.1")
    port = int(os.getenv("DUCKBOT_HYBRID_PORT", "8794"))
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()

