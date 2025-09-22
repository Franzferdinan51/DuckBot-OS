#!/usr/bin/env python3
"""
Classic DuckBot Enhanced Mode (stub)
Starts a simple FastAPI server to represent the classic enhanced mode.
"""
from __future__ import annotations

import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(title="DuckBot Classic Enhanced", version="1.0")


@app.get("/healthz")
def health() -> JSONResponse:
    return JSONResponse({"ok": True, "mode": "classic_enhanced"})


def main() -> None:
    host = os.getenv("DUCKBOT_CLASSIC_HOST", "127.0.0.1")
    port = int(os.getenv("DUCKBOT_CLASSIC_PORT", "8792"))
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()

