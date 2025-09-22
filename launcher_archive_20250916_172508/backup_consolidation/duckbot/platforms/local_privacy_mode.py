#!/usr/bin/env python3
"""
DuckBot Local-First Privacy Mode (stub)
Starts a simple FastAPI app indicating offline/local mode.
"""
from __future__ import annotations

import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(title="DuckBot Local Privacy Mode", version="1.0")


@app.get("/healthz")
def health() -> JSONResponse:
    return JSONResponse({"ok": True, "mode": "local_privacy", "network": "disabled"})


def main() -> None:
    host = os.getenv("DUCKBOT_LOCAL_HOST", "127.0.0.1")
    port = int(os.getenv("DUCKBOT_LOCAL_PORT", "8793"))
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()

