# duckbot/observability.py
import time
import os
from datetime import datetime, timezone
from fastapi import APIRouter, Response
from typing import Dict, Any
import asyncio

router = APIRouter()

# Simple in-memory metrics storage
_metrics = {
    "requests_total": 0,
    "errors_total": 0,
    "startup_time": time.time()
}

def increment_counter(name: str, labels: Dict[str, str] = None):
    """Increment a counter metric"""
    key = f"{name}_{hash(str(labels)) if labels else 'default'}"
    _metrics[key] = _metrics.get(key, 0) + 1
    _metrics["requests_total"] = _metrics.get("requests_total", 0) + 1

@router.get("/healthz")
async def health_check():
    """Health check endpoint for load balancers and monitoring"""
    uptime_seconds = time.time() - _metrics["startup_time"]
    
    health_data = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "uptime_seconds": int(uptime_seconds),
        "version": "3.0.4"
    }
    
    # Quick provider health checks (non-blocking)
    try:
        # Check if LM Studio is available
        import requests
        lm_response = await asyncio.wait_for(
            asyncio.create_task(asyncio.to_thread(
                requests.get, "http://localhost:1234/v1/models", timeout=2
            )), timeout=3.0
        )
        health_data["lm_studio"] = "healthy" if lm_response.status_code == 200 else "unhealthy"
    except:
        health_data["lm_studio"] = "unavailable"
    
    # Check if settings are loadable
    try:
        from duckbot.settings_gpt import load_settings
        settings = load_settings()
        health_data["settings"] = "healthy" if settings else "unhealthy"
    except:
        health_data["settings"] = "error"
    
    increment_counter("healthz_requests")
    return health_data

@router.get("/metrics")
async def metrics_endpoint():
    """Prometheus-style metrics endpoint"""
    uptime_seconds = time.time() - _metrics["startup_time"]
    
    metrics_text = f"""# HELP duckbot_uptime_seconds Total uptime in seconds
# TYPE duckbot_uptime_seconds gauge
duckbot_uptime_seconds {int(uptime_seconds)}

# HELP duckbot_requests_total Total number of requests
# TYPE duckbot_requests_total counter
duckbot_requests_total {_metrics.get('requests_total', 0)}

# HELP duckbot_errors_total Total number of errors
# TYPE duckbot_errors_total counter
duckbot_errors_total {_metrics.get('errors_total', 0)}

# HELP duckbot_healthz_requests_total Health check requests
# TYPE duckbot_healthz_requests_total counter
duckbot_healthz_requests_total {_metrics.get(f"healthz_requests_{hash('default')}", 0)}
"""
    
    increment_counter("metrics_requests")
    return Response(content=metrics_text, media_type="text/plain")

@router.get("/status")
async def detailed_status():
    """Detailed system status for debugging"""
    uptime_seconds = time.time() - _metrics["startup_time"]
    
    try:
        from duckbot.ai_router_gpt import get_router_state
        router_state = get_router_state()
    except:
        router_state = {"error": "router state unavailable"}
    
    # Add service detection
    services_status = {}
    try:
        from duckbot.service_detector import ServiceDetector
        detector = ServiceDetector()
        services_status = detector.get_all_service_status()
        recommendations = detector.get_startup_recommendations()
        services_status["_recommendations"] = recommendations
    except:
        services_status = {"error": "service detection unavailable"}
    
    return {
        "system": {
            "status": "operational",
            "uptime_seconds": int(uptime_seconds),
            "version": "3.0.4",
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        "metrics": {k: v for k, v in _metrics.items() if not k.startswith("startup")},
        "router": router_state,
        "services": services_status,
        "environment": {
            "python_version": os.sys.version.split()[0] if hasattr(os, 'sys') else "unknown"
        }
    }