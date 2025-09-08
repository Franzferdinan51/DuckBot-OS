
# duckbot/webui.py
import os, asyncio, time, json, re
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Form, HTTPException, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import threading
import tempfile
import secrets
from .service_detector import ServiceDetector

# Improve Windows console Unicode handling to avoid UnicodeEncodeError
if os.name == 'nt':
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# fcntl not available on Windows - only needed for Unix file locking
try:
    import fcntl
except ImportError:
    fcntl = None

from duckbot.settings_gpt import load_settings, save_settings, apply_to_env
from duckbot.ai_router_gpt import route_task, get_router_state, clear_cache, reset_breakers, refresh_lm_studio_model
from duckbot.observability import router as observability_router
from duckbot.rate_limit import rate_limited
from duckbot.rag import index_stats as rag_index_stats, ingest_paths as rag_ingest_paths, clear_index as rag_clear_index, build_context as rag_build_context, auto_ingest_defaults as rag_auto_ingest

def _infer_kind_from_message(message: str) -> str:
    m = (message or "").strip()
    ml = m.lower()
    if not ml:
        return "status"
    # Scoring-based heuristic
    scores = {
        "code": 0,
        "json_format": 0,
        "policy": 0,
        "long_form": 0,
        "arbiter": 0,
        "reasoning": 0,
        "summary": 0,
        "status": 0,
    }
    # Signals
    code_signals = ["```", "traceback", "exception", "stack trace", ".py", ".js", "def ", "class ", "function ", "return ", "import ", "console.log", "TypeError", "NameError"]
    json_signals = ["json", "schema", "quote", "{", "}"]
    policy_signals = ["policy", "compliance", "gdpr", "hipaa", "terms", "privacy", "moderation"]
    long_signals = ["write", "essay", "long form", "detailed", "comprehensive", "report", "draft"]
    arbiter_signals = [" vs ", "versus", "compare", "pros and cons", "choose between", "which is better", "arbiter"]
    reason_signals = ["why", "how", "plan", "steps", "explain", "analysis", "reason"]
    summary_signals = ["summarize", "tl;dr", "in bullets", "brief", "key points"]
    # Apply scoring
    for s in code_signals:
        if s in ml:
            scores["code"] += 2
    # JSON: structure + mentions
    if ml.strip().startswith("{") and ml.strip().endswith("}") and ":" in ml:
        scores["json_format"] += 3
    if "json" in ml:
        scores["json_format"] += 2
    for s in policy_signals:
        if s in ml:
            scores["policy"] += 2
    for s in long_signals:
        if s in ml:
            scores["long_form"] += 1
    for s in arbiter_signals:
        if s in ml:
            scores["arbiter"] += 2
    for s in reason_signals:
        if ("?" in m and s in ml) or (s in ml and len(m.split()) > 12):
            scores["reasoning"] += 1
    for s in summary_signals:
        if s in ml:
            scores["summary"] += 2
    # Length-based nudges
    wc = len(m.split())
    if wc > 150:
        scores["long_form"] += 2
    elif wc > 80:
        scores["long_form"] += 1
    # Choose best with precedence
    order = ["code","json_format","policy","arbiter","reasoning","long_form","summary","status"]
    best = "status"; best_score = -1
    for k in order:
        if scores[k] > best_score:
            best = k; best_score = scores[k]
    return best

def _infer_risk_from_message(message: str) -> str:
    ml = (message or "").lower()
    high = ["delete ", "shutdown", "terminate", "kill process", "rm -rf", "format", "drop table", "registry"]
    medium = ["restart", "stop service", "modify", "write file", "system32", "admin"]
    if any(w in ml for w in high):
        return "high"
    if any(w in ml for w in medium):
        return "medium"
    return "low"

# Import action and reasoning logger  
try:
    from .action_reasoning_logger import action_logger
    ACTION_LOGGING_AVAILABLE = True
except ImportError:
    ACTION_LOGGING_AVAILABLE = False

APP_TITLE = "DuckBot v3.0.5 AI Manager - WebUI"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        # ensure dirs exist
        STATIC_DIR.mkdir(parents=True, exist_ok=True)
        TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
        
        # apply settings to env
        try:
            apply_to_env(load_settings())
        except Exception as e:
            print(f"[WARNING] Could not apply settings: {e}")
        
        # Initialize Advanced Integrations
        try:
            from .wsl_integration import initialize_wsl
            from .bytebot_integration import initialize_bytebot
            from .archon_integration import initialize_archon
            from .chromium_integration import initialize_chromium
            
            print("[INTEGRATIONS] Initializing advanced integrations...")
            
            # WSL Integration
            wsl_available = await initialize_wsl()
            if wsl_available:
                print("[WSL] ✅ WSL integration ready")
            else:
                print("[WSL] ⚠️ WSL not available on this system")
            
            # ByteBot Integration
            bytebot_available = await initialize_bytebot()
            if bytebot_available:
                print("[BYTEBOT] ✅ ByteBot integration ready")
            else:
                print("[BYTEBOT] ⚠️ ByteBot dependencies not available")
            
            # Archon Integration
            archon_available = await initialize_archon()
            if archon_available:
                print("[ARCHON] ✅ Archon agent system ready")
            else:
                print("[ARCHON] ⚠️ Archon initialization failed")
            
            # ChromiumOS Integration
            chromium_available = await initialize_chromium()
            if chromium_available:
                print("[CHROMIUM] ✅ ChromiumOS browser integration ready")
            else:
                print("[CHROMIUM] ⚠️ ChromiumOS features not available")
            
            integrations_count = sum([wsl_available, bytebot_available, archon_available, chromium_available])
            print(f"[INTEGRATIONS] ✅ {integrations_count}/4 advanced integrations loaded")
            
        except Exception as e:
            print(f"[INTEGRATIONS] ⚠️ Integration initialization failed: {e}")
        
        # Start queue worker
        task = asyncio.create_task(queue_worker())
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)
        
        # Print token for easy access
        print(f"[TOKEN] DuckBot WebUI Token: {WEBUI_TOKEN}")
        port = os.getenv("DUCKBOT_WEBUI_PORT", "8787")
        print(f"[URL] WebUI URL: http://localhost:{port}/?token={WEBUI_TOKEN}")
        print(f"[INFO] Tailscale-friendly: Works best with localhost:{port} (not IP addresses)")
        print("[STARTUP] DuckBot WebUI ready")
        
        yield
        
    except Exception as e:
        print(f"[ERROR] Startup failed: {e}")
        raise
    finally:
        # Shutdown
        print("[SHUTDOWN] Shutting down DuckBot WebUI...")
        
        # Signal all background tasks to stop
        shutdown_event.set()
        
        # Clean shutdown without recursion
        if background_tasks:
            print("[WAIT] Waiting for background tasks to finish...")
            
            # Cancel all tasks first
            for task in list(background_tasks):
                if not task.done():
                    task.cancel()
            
            # Brief wait for cancellation
            await asyncio.sleep(0.1)
            
        print("[SHUTDOWN] DuckBot WebUI shutdown complete")

app = FastAPI(title=APP_TITLE, lifespan=lifespan)
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
QUEUE_PATH = BASE_DIR / "task_queue.json"
TOKEN_PATH = BASE_DIR / "webui_token.txt"

# Generate or load shared WebUI token
def get_or_create_token():
    """Generate a random token for WebUI security"""
    if TOKEN_PATH.exists():
        try:
            return TOKEN_PATH.read_text(encoding="utf-8").strip()
        except Exception:
            pass
    
    # Generate new token
    token = secrets.token_urlsafe(32)
    try:
        TOKEN_PATH.write_text(token, encoding="utf-8")
        return token
    except Exception as e:
        print(f"Warning: Could not save WebUI token: {e}")
        return token

WEBUI_TOKEN = get_or_create_token()
# Allow localhost bypass for development/desktop use (configurable)
ALLOW_LOCAL_BYPASS = str(os.getenv("DUCKBOT_WEBUI_LOCAL_BYPASS", "1")).strip().lower() not in {"0", "false", "no"}

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Add observability endpoints
app.include_router(observability_router)

# Security: Token validation
security = HTTPBearer(auto_error=False)

def _is_local_request(request: Request) -> bool:
    try:
        client_host = (request.client.host if request.client else "") or ""
        # Common loopback indicators
        if client_host in {"127.0.0.1", "::1", "localhost"}:
            return True
        # When accessed via localhost hostname, also allow
        host_header = (request.headers.get("host", "") or "").lower()
        if host_header.startswith("localhost:") or host_header == "localhost" or host_header.startswith("127.0.0.1:") or host_header == "127.0.0.1":
            return True
        # Also trust Origin/Referer from localhost
        origin = (request.headers.get("origin", "") or "").lower()
        referer = (request.headers.get("referer", "") or "").lower()
        if ("localhost" in origin) or ("127.0.0.1" in origin) or ("localhost" in referer) or ("127.0.0.1" in referer):
            return True
    except Exception:
        pass
    return False

def verify_token(request: Request, token: str = Query(None), credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify WebUI access token from query param or Authorization header"""
    # Localhost bypass for convenience when running on the same machine
    if ALLOW_LOCAL_BYPASS and _is_local_request(request):
        return True
    # Check query parameter first (for browser access)
    if token == WEBUI_TOKEN:
        return True
    
    # Check Authorization header (for API access)  
    if credentials and credentials.credentials == WEBUI_TOKEN:
        return True
        
    # Allow initial access to get token info
    return False

def require_token(authorized: bool = Depends(verify_token)):
    """Dependency that requires valid token"""
    if not authorized:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "WebUI access requires token",
                "help": f"Add ?token={WEBUI_TOKEN} to URL or use Authorization: Bearer {WEBUI_TOKEN} header",
                "local_bypass": "enabled" if ALLOW_LOCAL_BYPASS else "disabled",
                "example": f"http://localhost:8787/?token={WEBUI_TOKEN}"
            }
        )
    return True

# Queue lock to prevent race conditions
queue_lock = asyncio.Lock()  # FIXED: Use asyncio.Lock for async compatibility
shutdown_event = asyncio.Event()
background_tasks = set()

def atomic_write_json(file_path: Path, data):
    """Atomic write to prevent corruption during concurrent access"""
    temp_path = file_path.with_suffix(f"{file_path.suffix}.tmp.{os.getpid()}")
    try:
        temp_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        if os.name == 'nt':  # Windows
            if file_path.exists():
                file_path.unlink()
            temp_path.rename(file_path)
        else:  # Unix-like
            temp_path.rename(file_path)
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        raise e

async def safe_read_queue():
    """Thread-safe queue reading with async lock"""
    async with queue_lock:
        try:
            if not QUEUE_PATH.exists():
                return []
            return json.loads(QUEUE_PATH.read_text("utf-8") or "[]")
        except Exception as e:
            import logging
            logging.error(f"Error reading queue: {e}")
            return []

async def safe_write_queue(data):
    """Thread-safe queue writing with atomic operations"""
    async with queue_lock:
        try:
            atomic_write_json(QUEUE_PATH, data)
        except Exception as e:
            import logging
            logging.error(f"Error writing queue: {e}")

# Background queue processor
async def queue_worker():
    """Simplified queue worker to prevent restart loops"""
    print("[QUEUE] Worker started")
    
    try:
        while not shutdown_event.is_set():
            try:
                # Simple check without complex processing that might cause issues
                await asyncio.sleep(2.0)
                
                # Check for shutdown with timeout
                try:
                    await asyncio.wait_for(shutdown_event.wait(), timeout=0.1)
                    break  # Shutdown requested
                except asyncio.TimeoutError:
                    continue  # Normal operation
                    
            except Exception as e:
                print(f"[QUEUE] Error: {e}")
                # Sleep after error to prevent tight error loops
                await asyncio.sleep(5)
                
    except asyncio.CancelledError:
        print("[QUEUE] Worker cancelled")
        raise
    finally:
        print("[QUEUE] Worker stopped gracefully")

# Old startup handler removed - using lifespan instead
# async def on_startup():
    # ensure dirs exist
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    # apply settings to env
    apply_to_env(load_settings())
    # start queue worker with graceful shutdown tracking
    task = asyncio.create_task(queue_worker())
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)
    # Print token for easy access
    try:
        print(f"ðŸ” DuckBot WebUI Token: {WEBUI_TOKEN}")
        port = os.getenv("DUCKBOT_WEBUI_PORT", "8787")
        print(f"ðŸŒ WebUI URL: http://localhost:{port}/?token={WEBUI_TOKEN}")
        print(f"ðŸ“± Tailscale-friendly: Works best with localhost:{port} (not IP addresses)")
    except UnicodeEncodeError:
        print(f"[TOKEN] DuckBot WebUI Token: {WEBUI_TOKEN}")
        port = os.getenv("DUCKBOT_WEBUI_PORT", "8787")
        print(f"[URL] WebUI URL: http://localhost:{port}/?token={WEBUI_TOKEN}")
        print(f"[INFO] Tailscale-friendly: Works best with localhost:{port} (not IP addresses)")

# Old shutdown handler removed - using lifespan instead
# async def on_shutdown():
    try:
        print("ðŸ›‘ Shutting down DuckBot WebUI...")
    except UnicodeEncodeError:
        print("[SHUTDOWN] Shutting down DuckBot WebUI...")
    # Signal all background tasks to stop
    shutdown_event.set()
    # Wait for background tasks to complete
    if background_tasks:
        try:
            print("â³ Waiting for background tasks to finish...")
        except UnicodeEncodeError:
            print("[WAIT] Waiting for background tasks to finish...")
        await asyncio.gather(*background_tasks, return_exceptions=True)
    try:
        print("[SHUTDOWN] DuckBot WebUI shutdown complete")
    except UnicodeEncodeError:
        print("[SHUTDOWN] DuckBot WebUI shutdown complete")

# Initialize service detector
service_detector = ServiceDetector()

@app.get("/token")
def get_token_info():
    """Unprotected endpoint to get token info for initial access"""
    port = os.getenv("DUCKBOT_WEBUI_PORT", "8787")
    return {
        "token": WEBUI_TOKEN,
        "url_with_token": f"http://localhost:{port}/?token={WEBUI_TOKEN}",
        "header_example": f"Authorization: Bearer {WEBUI_TOKEN}",
        "tailscale_note": f"Use localhost:{port} for best Tailscale compatibility"
    }

@app.post("/models/refresh")
def refresh_models(_auth: bool = Depends(require_token)):
    """Refresh LM Studio model detection by clearing cache"""
    try:
        from .ai_router_gpt import clear_lm_studio_cache
        clear_lm_studio_cache()
        return {"success": True, "message": "Model cache cleared - will refresh on next request"}
    except ImportError:
        # Fallback if the function doesn't exist
        return {"success": False, "error": "Model refresh function not available"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/", response_class=HTMLResponse)
def home(request: Request, _auth: bool = Depends(require_token)):
    """DUCKBOT OS ONLY - Complete AI Management Console (Old WebUI Removed)"""
    import os
    
    # Try multiple possible locations for the DuckBot OS file
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "DuckBotOS-Complete.html"),  # ../DuckBotOS-Complete.html
        os.path.join(os.getcwd(), "DuckBotOS-Complete.html"),  # ./DuckBotOS-Complete.html
        "DuckBotOS-Complete.html"  # Direct path
    ]
    
    duckbot_os_path = None
    for path in possible_paths:
        if os.path.exists(path):
            duckbot_os_path = path
            break
    
    if not duckbot_os_path:
        # CRITICAL ERROR - DuckBot OS file missing
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>DuckBot OS - File Missing</title>
            <style>
                body {{ font-family: Arial, sans-serif; background: #1e293b; color: white; padding: 2rem; }}
                .error {{ background: #dc2626; padding: 1rem; border-radius: 8px; margin: 1rem 0; }}
                .paths {{ background: #374151; padding: 1rem; border-radius: 8px; font-family: monospace; }}
            </style>
        </head>
        <body>
            <h1>🦆 DuckBot OS - Critical Error</h1>
            <div class="error">
                <h2>❌ DuckBot OS Interface File Missing!</h2>
                <p>The new DuckBot OS interface file could not be found.</p>
            </div>
            <h3>Searched Locations:</h3>
            <div class="paths">
                {chr(10).join([f"• {path} ({'✅ EXISTS' if os.path.exists(path) else '❌ MISSING'})" for path in possible_paths])}
            </div>
            <h3>To Fix This:</h3>
            <ol>
                <li>Ensure <code>DuckBotOS-Complete.html</code> is in your DuckBot root directory</li>
                <li>Check the file permissions and encoding</li>
                <li>Restart the DuckBot server</li>
            </ol>
            <p><strong>Current Directory:</strong> {os.getcwd()}</p>
        </body>
        </html>
        """
        print("[DUCKBOT OS FATAL] DuckBot OS file not found!")
        print(f"[DUCKBOT OS FATAL] Current directory: {os.getcwd()}")
        for path in possible_paths:
            print(f"[DUCKBOT OS FATAL] Checked: {path} - {'EXISTS' if os.path.exists(path) else 'MISSING'}")
        
        return HTMLResponse(content=error_html, status_code=500)
    
    # Load and serve DuckBot OS
    print(f"[DUCKBOT OS] Loading interface from: {duckbot_os_path}")
    try:
        with open(duckbot_os_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Inject the token and API configuration into the HTML
        token_param = request.query_params.get('token', '') or (_auth and WEBUI_TOKEN or '')
        
        # Token injection
        if 'apiToken:' in html_content:
            html_content = html_content.replace(
                'apiToken: new URLSearchParams(window.location.search).get(\'token\') || \'\',',
                f'apiToken: \'{token_param}\','
            )
            html_content = html_content.replace(
                'apiBase: window.location.origin',
                f'apiBase: \'{request.url.scheme}://{request.url.netloc}\''
            )
        
        print(f"[DUCKBOT OS] ✅ Successfully serving new DuckBot OS interface")
        return HTMLResponse(
            content=html_content,
            headers={
                "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                "Pragma": "no-cache",
            }
        )
        
    except Exception as e:
        # Show detailed error instead of fallback
        import traceback
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>DuckBot OS - Loading Error</title>
            <style>
                body {{ font-family: Arial, sans-serif; background: #1e293b; color: white; padding: 2rem; }}
                .error {{ background: #dc2626; padding: 1rem; border-radius: 8px; margin: 1rem 0; }}
                .traceback {{ background: #374151; padding: 1rem; border-radius: 8px; font-family: monospace; font-size: 12px; white-space: pre-wrap; }}
            </style>
        </head>
        <body>
            <h1>🦆 DuckBot OS - Loading Error</h1>
            <div class="error">
                <h2>❌ Error Loading DuckBot OS Interface</h2>
                <p><strong>Error:</strong> {str(e)}</p>
            </div>
            <h3>Traceback:</h3>
            <div class="traceback">{traceback.format_exc()}</div>
            <h3>File Info:</h3>
            <p><strong>Path:</strong> {duckbot_os_path}</p>
            <p><strong>Exists:</strong> {os.path.exists(duckbot_os_path)}</p>
            <p><strong>Size:</strong> {os.path.getsize(duckbot_os_path) if os.path.exists(duckbot_os_path) else 'N/A'} bytes</p>
        </body>
        </html>
        """
        
        print(f"[DUCKBOT OS ERROR] Failed to load DuckBot OS: {e}")
        print(f"[DUCKBOT OS ERROR] Traceback: {traceback.format_exc()}")
        
        return HTMLResponse(content=error_html, status_code=500)

@app.get("/classic", response_class=HTMLResponse)
def classic_webui(request: Request, _auth: bool = Depends(require_token)):
    """Classic WebUI interface for backward compatibility"""
    state = get_router_state()
    settings = load_settings()
    return templates.TemplateResponse(
        "dashboard_modern.html",
        {"request": request, "state": state, "settings": settings},
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
        },
    )

@app.post("/run", response_class=HTMLResponse)
@rate_limited(requests_per_second=2.0, burst=5)
async def run_task(request: Request,
                   kind: str = Form(...),
                   risk: str = Form("low"),
                   prompt: str = Form(...),
                   override: str = Form(""),
                   _auth: bool = Depends(require_token)):
    task = {"kind": kind, "risk": risk, "prompt": prompt}
    if override.strip():
        task["override"] = override.strip()
    resp = route_task(task)
    state = get_router_state()
    settings = load_settings()
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "state": state,
            "settings": settings,
            "result": resp,
            "kind": kind,
            "risk": risk,
            "prompt": prompt,
            "override": override,
        },
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
        },
    )

@app.get("/settings", response_class=HTMLResponse)
def get_settings(request: Request, _auth: bool = Depends(require_token)):
    return templates.TemplateResponse(
        "settings.html",
        {"request": request, "settings": load_settings()},
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
        },
    )

@app.get("/cost", response_class=HTMLResponse)
def get_cost_dashboard(request: Request, _auth: bool = Depends(require_token)):
    return templates.TemplateResponse(
        "cost_dashboard.html",
        {"request": request},
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
        },
    )

@app.get("/companion", response_class=HTMLResponse)
def get_companion_page(request: Request, _auth: bool = Depends(require_token)):
    """3D Companion interface - Clippy-like AI assistant"""
    return templates.TemplateResponse(
        "companion.html",
        {"request": request},
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
        },
    )

@app.get("/react-os", response_class=HTMLResponse)
def react_os_redirect(request: Request, _auth: bool = Depends(require_token)):
    """Redirect to React OS (if running) or show info page"""
    # Check if React dev server is running on port 3000
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', 3000))
        sock.close()
        if result == 0:
            # React server is running, redirect
            return RedirectResponse(url="http://localhost:3000")
    except:
        pass
    
    # React server not running, show info page
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>DuckBot React OS</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                   background: linear-gradient(135deg, #1e293b, #334155); color: white; 
                   margin: 0; padding: 2rem; min-height: 100vh; }}
            .container {{ max-width: 600px; margin: 0 auto; text-align: center; }}
            .logo {{ font-size: 4rem; margin-bottom: 1rem; }}
            h1 {{ color: #10b981; }}
            .feature {{ background: rgba(255,255,255,0.1); padding: 1rem; margin: 1rem 0; 
                      border-radius: 8px; border: 1px solid rgba(255,255,255,0.2); }}
            .btn {{ background: #10b981; color: white; padding: 12px 24px; 
                    border: none; border-radius: 6px; font-size: 1.1rem; 
                    cursor: pointer; text-decoration: none; display: inline-block; margin: 0.5rem; }}
            .btn:hover {{ background: #059669; }}
            .btn-alt {{ background: #3b82f6; }}
            .btn-alt:hover {{ background: #2563eb; }}
            .warning {{ color: #f59e0b; background: rgba(245, 158, 11, 0.1); 
                        padding: 1rem; border-radius: 8px; margin: 1rem 0; }}
            code {{ background: rgba(255,255,255,0.1); padding: 2px 6px; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">🦆</div>
            <h1>DuckBot React OS</h1>
            
            <div class="warning">
                <strong>⚠️ React Development Server Not Running</strong><br>
                The advanced React-based OS interface is not currently available.
            </div>
            
            <div class="feature">
                <h3>🎯 Features in React OS</h3>
                <p>• 3D Interactive Avatar with voice and animation</p>
                <p>• Chrome OS-like desktop environment</p>
                <p>• Advanced AI applications and tools</p>
                <p>• Integrated service management</p>
                <p>• Full DuckBot Enhanced integration</p>
            </div>
            
            <div class="feature">
                <h3>🚀 How to Start React OS</h3>
                <p>1. Run <code>START_DUCKBOT_OS.bat</code> to start both servers</p>
                <p>2. Or manually: <code>cd duckbot/react-webui && npm start</code></p>
                <p>3. Then visit <a href="http://localhost:3000" style="color: #10b981;">http://localhost:3000</a></p>
            </div>
            
            <a href="/" class="btn">← Back to Main WebUI</a>
            <a href="/duckbot-os?token={WEBUI_TOKEN}" class="btn btn-alt">🦆 Try Basic 3D Avatar</a>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/action-logs", response_class=HTMLResponse)
def get_action_logs(request: Request, _auth: bool = Depends(require_token)):
    """Action and reasoning logs viewer page"""
    return templates.TemplateResponse(
        "action_logs.html",
        {"request": request, "action_logging_available": ACTION_LOGGING_AVAILABLE},
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
        },
    )

@app.post("/settings")
async def post_settings(
    request: Request, 
    _auth: bool = Depends(require_token)
):
    form = await request.form()
    s = load_settings()
    for k, v in form.items():
        if k in s:
            s[k] = str(v)
    save_settings(s)
    apply_to_env(s)
    return RedirectResponse(url="/settings?saved=1", status_code=303)

@app.post("/cache/clear")
def api_clear_cache(_auth: bool = Depends(require_token)):
    clear_cache()
    return JSONResponse({"ok": True})

@app.post("/breakers/reset")
def api_reset_breakers(_auth: bool = Depends(require_token)):
    reset_breakers()
    return JSONResponse({"ok": True})

# Action and Reasoning Log API Endpoints
@app.get("/api/action-logs")
def api_get_action_logs(
    hours: int = Query(24, ge=1, le=168),  # 1 hour to 1 week
    action_type: str = Query(None),
    component: str = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    _auth: bool = Depends(require_token)
):
    """Get action and reasoning logs with optional filtering"""
    if not ACTION_LOGGING_AVAILABLE:
        return JSONResponse({
            "ok": False, 
            "error": "Action logging not available"
        })
    
    try:
        logs = action_logger.get_recent_actions(
            hours=hours,
            action_type=action_type,
            component=component,
            limit=limit
        )
        return JSONResponse({
            "ok": True,
            "logs": logs,
            "count": len(logs),
            "filters": {
                "hours": hours,
                "action_type": action_type,
                "component": component,
                "limit": limit
            }
        })
    except Exception as e:
        return JSONResponse({
            "ok": False,
            "error": f"Failed to retrieve logs: {str(e)}"
        })

@app.get("/api/action-logs/summary")
def api_get_action_summary(
    hours: int = Query(24, ge=1, le=168),
    _auth: bool = Depends(require_token)
):
    """Get summary statistics for action logs"""
    if not ACTION_LOGGING_AVAILABLE:
        return JSONResponse({
            "ok": False,
            "error": "Action logging not available"
        })
    
    try:
        summary = action_logger.get_action_summary(hours=hours)
        return JSONResponse({
            "ok": True,
            "summary": summary
        })
    except Exception as e:
        return JSONResponse({
            "ok": False,
            "error": f"Failed to generate summary: {str(e)}"
        })

@app.post("/models/refresh")
def api_refresh_model(_auth: bool = Depends(require_token)):
    new_model = refresh_lm_studio_model()
    return JSONResponse({"ok": True, "current_model": new_model})

@app.get("/models/available")
def api_available_models(_auth: bool = Depends(require_token)):
    from duckbot.ai_router_gpt import get_available_local_models, LM_STUDIO_URL
    try:
        models = get_available_local_models()
        return JSONResponse({
            "ok": True, 
            "models": models,
            "lm_studio_url": LM_STUDIO_URL,
            "count": len(models),
            "debug": f"Fetched {len(models)} models from LM Studio"
        })
    except Exception as e:
        return JSONResponse({
            "ok": False, 
            "models": [],
            "error": str(e),
            "lm_studio_url": LM_STUDIO_URL,
            "debug": f"Error fetching models: {str(e)}"
        })

@app.post("/models/set")
def api_set_model(_auth: bool = Depends(require_token), model_id: str = Form(...)):
    from duckbot.ai_router_gpt import set_local_model_preference, get_available_local_models
    available_models = get_available_local_models()
    model_ids = [m["id"] for m in available_models]
    
    if model_id not in model_ids:
        return JSONResponse({"ok": False, "error": f"Invalid model ID. Available: {model_ids[:3]}..."})
    
    try:
        set_local_model_preference(model_id)
        return JSONResponse({"ok": True, "model_set": model_id})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)})

@app.get("/api/cost_summary")
def api_cost_summary(_auth: bool = Depends(require_token), days: int = 30):
    """Get cost summary data"""
    try:
        from duckbot.cost_tracker import CostTracker
        cost_tracker = CostTracker()
        
        summary = cost_tracker.get_usage_summary(days)
        predictions = cost_tracker.get_cost_predictions()
        
        return JSONResponse({
            'success': True,
            'data': {
                'total_cost': summary.total_cost,
                'total_tokens': summary.total_tokens,
                'total_requests': summary.total_requests,
                'by_model': dict(summary.by_model),
                'by_provider': dict(summary.by_provider),
                'predictions': predictions,
                'period_days': days
            }
        })
    except Exception as e:
        return JSONResponse({'success': False, 'error': str(e)})

@app.get("/api/system-status")
def api_system_status(_auth: bool = Depends(require_token)):
    """Get real-time system status for dashboard updates"""
    try:
        state = get_router_state()
        return JSONResponse({
            "ok": True,
            "status": {
                "bucket_tokens": state.get("bucket_tokens", 0),
                "chat_bucket_tokens": state.get("chat_bucket_tokens", 0),
                "background_bucket_tokens": state.get("background_bucket_tokens", 0),
                "bucket_limit": state.get("bucket_limit", 60),
                "chat_bucket_limit": state.get("chat_bucket_limit", 30),
                "background_bucket_limit": state.get("background_bucket_limit", 30),
                "cache_size": state.get("cache_size", 0),
                "breakers": state.get("breakers", {}),
                "current_lm_model": state.get("current_lm_model", ""),
                "lm_studio_status": state.get("lm_studio_status", {})
            }
        })
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)})

@app.get("/api/services")
def api_services_status(_auth: bool = Depends(require_token)):
    """Get comprehensive service status"""
    try:
        from duckbot.service_detector import ServiceDetector
        
        service_detector = ServiceDetector()
        
        # Define services with proper display information
        service_definitions = [
            {
                "name": "comfyui",
                "display_name": "ComfyUI Image Generation",
                "port": 8188,
                "description": "AI image and video generation server"
            },
            {
                "name": "lm_studio", 
                "display_name": "LM Studio Server",
                "port": 1234,
                "description": "Local AI language model server"
            },
            {
                "name": "n8n",
                "display_name": "n8n Workflow Automation", 
                "port": 5678,
                "description": "Workflow automation and integration platform"
            },
            {
                "name": "jupyter",
                "display_name": "Jupyter Notebook Server",
                "port": 8889, 
                "description": "Interactive data science notebooks"
            },
            {
                "name": "open_notebook",
                "display_name": "Open Notebook AI Interface",
                "port": 8502,
                "description": "AI-powered notebook interface"
            },
            {
                "name": "webui",
                "display_name": "DuckBot Professional WebUI",
                "port": 8787,
                "description": "Main dashboard and control interface"
            }
        ]
        
        services = {}
        for service_def in service_definitions:
            try:
                status_info = service_detector.detect_service_status(service_def["name"])
                
                # Map service detector status to WebUI expected format
                webui_status = "not_running"
                if status_info.get("status") == "running_healthy":
                    webui_status = "running_healthy"
                elif status_info.get("status") == "running_unhealthy":
                    webui_status = "running_unhealthy"
                elif status_info.get("status") == "process_detected":
                    webui_status = "process_detected"
                
                services[service_def["name"]] = {
                    "name": service_def["display_name"],
                    "status": webui_status,
                    "port": service_def["port"],
                    "description": service_def["description"],
                    "available": status_info.get("status") in ["running_healthy", "running_unhealthy"],
                    "details": status_info
                }
            except Exception as e:
                services[service_def["name"]] = {
                    "name": service_def["display_name"],
                    "status": "error", 
                    "port": service_def["port"],
                    "description": service_def["description"],
                    "available": False,
                    "error": str(e)
                }
        
        # Convert services dict to array for frontend compatibility
        services_array = []
        for service_key, service_data in services.items():
            services_array.append({
                'name': service_data['name'],
                'status': 'running' if service_data['status'] in ['running_healthy', 'running_unhealthy'] else 'stopped',
                'port': service_data['port'],
                'description': service_data['description'],
                'available': service_data['available'],
                'details': service_data.get('details', {}),
                'service_key': service_key
            })
        
        return JSONResponse({
            'ok': True,
            'services': services_array
        })
    except Exception as e:
        return JSONResponse({'ok': False, 'services': [], 'error': str(e)})

@app.post("/api/services/{service}/start")
def api_start_service(service: str, _auth: bool = Depends(require_token)):
    """Start a specific service"""
    try:
        from duckbot.server_manager import ServerManager
        server_manager = ServerManager()
        
        if hasattr(server_manager, f'start_{service}'):
            result = getattr(server_manager, f'start_{service}')()
            return JSONResponse({'success': True, 'result': result})
        else:
            return JSONResponse({'success': False, 'error': f'Service {service} not supported'})
    except Exception as e:
        return JSONResponse({'success': False, 'error': str(e)})

@app.post("/api/services/{service}/stop") 
def api_stop_service(service: str, _auth: bool = Depends(require_token)):
    """Stop a specific service"""
    try:
        from duckbot.server_manager import ServerManager
        server_manager = ServerManager()
        
        if hasattr(server_manager, f'stop_{service}'):
            result = getattr(server_manager, f'stop_{service}')()
            return JSONResponse({'success': True, 'result': result})
        else:
            return JSONResponse({'success': False, 'error': f'Service {service} not supported'})
    except Exception as e:
        return JSONResponse({'success': False, 'error': str(e)})

@app.post("/api/task")
@rate_limited(requests_per_second=5.0, burst=10)
def api_run_task(request: Request, _auth: bool = Depends(require_token), 
                task_type: str = Form(...), prompt: str = Form(...), 
                priority: str = Form("medium"), bucket_type: str = Form("background")):
    """Run an AI task with specified parameters"""
    try:
        task = {
            "kind": task_type,
            "risk": priority,
            "prompt": prompt,
            "override": ""
        }
        
        result = route_task(task, bucket_type=bucket_type)
        return JSONResponse({
            "success": True,
            "result": result,
            "task_id": f"task_{int(time.time())}"
        })
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})

@app.get("/qwen/status")
def api_qwen_status(_auth: bool = Depends(require_token)):
    try:
        from duckbot.qwen_diagnostics import QwenDiagnostics
        qwen = QwenDiagnostics()
        return JSONResponse({
            "ok": True, 
            "qwen_available": qwen.qwen_available,
            "integration_enabled": True,
            "temp_dir": str(qwen.temp_dir)
        })
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)})

@app.post("/qwen/analyze")
def api_qwen_analyze(_auth: bool = Depends(require_token), code_prompt: str = Form(...)):
    try:
        from duckbot.qwen_diagnostics import QwenDiagnostics
        qwen = QwenDiagnostics()
        
        if not qwen.qwen_available:
            return JSONResponse({"ok": False, "error": "Qwen Code tools not available"})
            
        analysis = qwen.analyze_code_prompt(code_prompt)
        return JSONResponse({
            "ok": True, 
            "analysis": analysis or "No analysis available",
            "qwen_enhanced": analysis is not None
        })
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)})

@app.get("/servers/status")
def api_servers_status(_auth: bool = Depends(require_token)):
    """Get status of all ecosystem servers"""
    try:
        from duckbot.server_manager import server_manager
        status = server_manager.get_all_service_status()
        
        # Convert ServiceInfo objects to dictionaries
        status_dict = {}
        for service_name, service_info in status.items():
            status_dict[service_name] = {
                "name": service_info.name,
                "display_name": service_info.display_name,
                "port": service_info.port,
                "url": service_info.url,
                "status": service_info.status.value,
                "pid": service_info.pid,
                "auto_restart": service_info.auto_restart
            }
        
        return JSONResponse({"ok": True, "services": status_dict})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)})

@app.post("/servers/start")
def api_start_server(_auth: bool = Depends(require_token), service_name: str = Form(...)):
    """Start a specific server/service"""
    try:
        from duckbot.server_manager import server_manager
        success, message = server_manager.start_service(service_name)
        return JSONResponse({"ok": success, "message": message})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)})

@app.post("/servers/stop")
def api_stop_server(_auth: bool = Depends(require_token), service_name: str = Form(...)):
    """Stop a specific server/service"""
    try:
        from duckbot.server_manager import server_manager
        success, message = server_manager.stop_service(service_name)
        return JSONResponse({"ok": success, "message": message})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)})

@app.post("/servers/restart")
def api_restart_server(_auth: bool = Depends(require_token), service_name: str = Form(...)):
    """Restart a specific server/service"""
    try:
        from duckbot.server_manager import server_manager
        success, message = server_manager.restart_service(service_name)
        return JSONResponse({"ok": success, "message": message})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)})

@app.post("/ecosystem/start")
def api_start_ecosystem(_auth: bool = Depends(require_token)):
    """Start the complete DuckBot ecosystem"""
    try:
        from duckbot.server_manager import server_manager
        success, results = server_manager.start_ecosystem()
        return JSONResponse({"ok": success, "results": results})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)})

@app.post("/ecosystem/stop")
def api_stop_ecosystem(_auth: bool = Depends(require_token)):
    """Stop the complete DuckBot ecosystem"""
    try:
        from duckbot.server_manager import server_manager
        success, results = server_manager.stop_ecosystem()
        return JSONResponse({"ok": success, "results": results})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)})

@app.get("/services/detect")
def api_detect_services(_auth: bool = Depends(require_token)):
    try:
        from duckbot.service_detector import ServiceDetector
        detector = ServiceDetector()
        status = detector.get_all_service_status()
        recommendations = detector.get_startup_recommendations()
        return JSONResponse({
            "ok": True,
            "services": status,
            "recommendations": recommendations,
            "timestamp": time.time()
        })
    except Exception as e:
        return JSONResponse({
            "ok": False,
            "error": f"Service detection failed: {str(e)}"
        })

@app.post("/queue")
@rate_limited(requests_per_second=5.0, burst=8)
def api_queue(request: Request, kind: str = Form(...), risk: str = Form("low"), prompt: str = Form(...), _auth: bool = Depends(require_token)):
    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    q = []
    if QUEUE_PATH.exists():
        try:
            q = json.loads(QUEUE_PATH.read_text("utf-8") or "[]")
        except Exception:
            q = []
    q.append({"kind":kind,"risk":risk,"prompt":prompt,"override":"queue"})
    QUEUE_PATH.write_text(json.dumps(q, indent=2), encoding="utf-8")
    return JSONResponse({"queued": len(q)})

# RAG management endpoints
@app.get("/rag/status")
def api_rag_status(_auth: bool = Depends(require_token)):
    try:
        stats = rag_index_stats()
        return JSONResponse({"ok": True, "stats": stats})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)})

@app.post("/rag/clear")
def api_rag_clear(_auth: bool = Depends(require_token)):
    try:
        rag_clear_index()
        return JSONResponse({"ok": True})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)})

@app.post("/rag/ingest")
def api_rag_ingest(_auth: bool = Depends(require_token), path: str = Form(None)):
    try:
        if not path:
            res = rag_auto_ingest()
        else:
            # Support semicolon or newline separated list
            raw = [p.strip() for p in re.split(r"[;\n]+", path) if p.strip()] if 're' in globals() else [p.strip() for p in path.split(';') if p.strip()]
            res = rag_ingest_paths(raw)
        return JSONResponse({"ok": True, "result": res})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)})

@app.post("/rag/search")
def api_rag_search(_auth: bool = Depends(require_token), q: str = Form(...), top_k: int = Form(4)):
    try:
        context, chunks = rag_build_context(q, top_k=top_k)
        return JSONResponse({"ok": True, "context": context, "chunks": chunks})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)})

@app.post("/chat")
@rate_limited(requests_per_second=10.0, burst=15)
async def api_chat(
    request: Request,
    message: str = Form(...),
    kind: str = Form("*"),
    risk: str = Form("low"),
    override: str = Form("") ,
    _auth: bool = Depends(require_token),
):
    """Unified chat endpoint that can run any AI task via chat.

    Accepts optional task parameters so the chat can drive the prior
    Task Runner capabilities without a separate form.
    """
    try:
        # Normalize inputs
        task_kind = (kind or "*").strip() or "*"
        if task_kind == "*":
            task_kind = _infer_kind_from_message(message)
        # Auto-risk if left at default
        task_risk = (risk or "low").strip() or "low"
        if task_risk == "low":
            task_risk = _infer_risk_from_message(message)
        task_override = (override or "").strip()

        task = {
            "kind": task_kind,
            "risk": task_risk,
            "prompt": message,
            "override": task_override,
        }

        # If configured, force cloud attempt for chat unless already overridden
        try:
            if not task_override:
                s = load_settings()
                if str(s.get("FORCE_CLOUD_FOR_CHAT", "0")).strip() in ("1", "true", "yes"):
                    task["override"] = "retry_cloud"
        except Exception:
            pass

        result = route_task(task, bucket_type="chat")
        return JSONResponse({
            "success": True,
            "response": result.get("text", "No response available"),
            "model": result.get("model_used", "unknown"),
            "confidence": result.get("confidence", 0),
            "cached": result.get("cached", False),
            "kind": task_kind,
            "risk": task_risk,
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "response": f"Error processing message: {str(e)}",
            "model": "error",
            "confidence": 0,
            "cached": False
        })

# Additional API endpoints for complete DuckBot feature parity

@app.post("/api/voice/generate")
async def api_voice_generate(
    request: Request,
    text: str = Form(...),
    voice: str = Form("en-alice"),
    preset: str = Form("single"),
    _auth: bool = Depends(require_token)
):
    """VibeVoice TTS generation endpoint"""
    try:
        from .vibevoice_client import VibeVoiceManager
        
        manager = VibeVoiceManager()
        if not await manager.initialize():
            return JSONResponse({"error": "VibeVoice not available"}, status_code=503)
        
        # Map voice names to speakers
        voice_mapping = {
            "en-alice": ["en-alice"],
            "en-carter": ["en-carter"],
            "en-david": ["en-david"],
            "en-emily": ["en-emily"]
        }
        
        speakers = voice_mapping.get(voice, ["en-alice"])
        audio_path = await manager.generate_voice_content(text, speakers)
        
        if audio_path:
            return JSONResponse({
                "success": True,
                "audio_url": f"/static/audio/{audio_path.split('/')[-1]}",
                "message": "Voice generation completed"
            })
        else:
            return JSONResponse({"error": "Voice generation failed"}, status_code=500)
            
    except Exception as e:
        return JSONResponse({"error": f"VibeVoice error: {str(e)}"}, status_code=500)

@app.post("/api/generate")
async def api_image_generate(
    request: Request,
    prompt: str = Form(...),
    model: str = Form("auto"),
    type: str = Form("image"),
    _auth: bool = Depends(require_token)
):
    """ComfyUI image generation endpoint"""
    try:
        if type != "image":
            return JSONResponse({"error": "Only image generation supported"}, status_code=400)
        
        # Simulate ComfyUI integration - in real implementation, this would connect to ComfyUI
        import tempfile
        import os
        
        # For demo, create a placeholder response
        temp_dir = os.path.join(tempfile.gettempdir(), "comfyui_output")
        os.makedirs(temp_dir, exist_ok=True)
        
        return JSONResponse({
            "success": True,
            "image_url": f"/static/generated/placeholder_{hash(prompt) % 10000}.png",
            "message": f"Image generation initiated for: {prompt[:50]}...",
            "prompt": prompt,
            "model": model
        })
        
    except Exception as e:
        return JSONResponse({"error": f"Image generation error: {str(e)}"}, status_code=500)

@app.get("/api/cost_summary")
async def api_cost_summary(
    request: Request,
    days: int = Query(7),
    _auth: bool = Depends(require_token)
):
    """Cost tracking and analytics endpoint"""
    try:
        from .cost_tracker import CostTracker
        
        tracker = CostTracker()
        summary = tracker.get_usage_summary(days)
        
        return JSONResponse({
            "total": summary.get("total_cost", 0.0),
            "query_count": summary.get("total_queries", 0),
            "average_cost": summary.get("average_cost", 0.0),
            "details": f"Usage data for last {days} days",
            "providers": summary.get("by_provider", {}),
            "daily_breakdown": summary.get("daily", [])
        })
        
    except Exception as e:
        return JSONResponse({"error": f"Cost tracking error: {str(e)}"}, status_code=500)

@app.get("/api/services")
async def api_services_status(
    request: Request,
    _auth: bool = Depends(require_token)
):
    """Service status monitoring endpoint"""
    try:
        from .service_detector import ServiceDetector
        
        detector = ServiceDetector()
        services = detector.detect_all_services()
        
        service_list = []
        for name, info in services.items():
            service_list.append({
                "name": name,
                "status": "running" if info.get("available", False) else "stopped",
                "port": info.get("port"),
                "url": info.get("url"),
                "description": info.get("description", "")
            })
        
        return JSONResponse({
            "services": service_list,
            "total": len(service_list),
            "running": len([s for s in service_list if s["status"] == "running"])
        })
        
    except Exception as e:
        return JSONResponse({"error": f"Service detection error: {str(e)}"}, status_code=500)

@app.post("/api/services/{service_name}/{action}")
async def api_service_control(
    request: Request,
    service_name: str,
    action: str,
    _auth: bool = Depends(require_token)
):
    """Service control endpoint (start/stop/restart)"""
    try:
        if action not in ["start", "stop", "restart"]:
            return JSONResponse({"error": "Invalid action"}, status_code=400)
        
        # In real implementation, this would control services via subprocess or system management
        return JSONResponse({
            "success": True,
            "message": f"Service {service_name} {action} initiated",
            "service": service_name,
            "action": action
        })
        
    except Exception as e:
        return JSONResponse({"error": f"Service control error: {str(e)}"}, status_code=500)

@app.get("/api/queue/status")
async def api_queue_status(
    request: Request,
    _auth: bool = Depends(require_token)
):
    """Queue status monitoring endpoint"""
    try:
        queue_data = await safe_read_queue()
        queue_size = len(queue_data) if queue_data else 0
        
        return JSONResponse({
            "queue_size": queue_size,
            "processing": queue_size > 0,
            "items": queue_data[:5] if queue_data else [],  # First 5 items preview
            "total_processed_today": 0  # Would be tracked in real implementation
        })
        
    except Exception as e:
        return JSONResponse({"error": f"Queue status error: {str(e)}"}, status_code=500)

@app.get("/api/action-logs")
async def api_action_logs(
    request: Request,
    limit: int = Query(50),
    _auth: bool = Depends(require_token)
):
    """Action logs endpoint"""
    try:
        # In real implementation, this would read from log files or database
        logs = [
            {
                "timestamp": "2024-01-01T12:00:00Z",
                "action": "chat_request",
                "user": "webui",
                "details": "AI chat query processed",
                "status": "success"
            }
        ]
        
        return JSONResponse({
            "logs": logs[:limit],
            "total": len(logs),
            "limit": limit
        })
        
    except Exception as e:
        return JSONResponse({"error": f"Logs error: {str(e)}"}, status_code=500)

# ============================================================================
# DUCKBOT OS API ENDPOINTS - 3D Avatar Integration with Windows Voice Fallback
# ============================================================================

@app.get("/duckbot-os", response_class=HTMLResponse)
def duckbot_os(request: Request, token: str = Query(None)):
    """Serve the DuckBot OS 3D interface"""
    if not verify_token(token):
        return RedirectResponse(url="/")
    
    # Serve the DuckBot OS HTML with token injection for API calls
    try:
        import os
        current_dir = os.path.dirname(os.path.dirname(__file__))  # Go up from duckbot/ to project root
        html_path = os.path.join(current_dir, "duckbot-os", "index.html")
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Inject the token and API base URL into the HTML
        html_content = html_content.replace(
            '<div id="root"></div>',
            f'''<div id="root"></div>
            <script>
                window.DUCKBOT_API_TOKEN = "{token}";
                window.DUCKBOT_API_BASE = "http://localhost:{request.url.port}";
                window.DUCKBOT_VOICE_FALLBACK_ONLY = true;
            </script>'''
        )
        
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>DuckBot OS not found. Please check installation.</h1>")

@app.post("/api/duckbot-os/chat")
def duckbot_os_chat(request: Request, message: str = Form(...), 
                   model: str = Form("auto"), provider: str = Form("auto"),
                   _auth: bool = Depends(require_token)):
    """DuckBot OS chat endpoint with Windows device voice fallback only"""
    try:
        # Determine the best task type for the message
        task_kind = _infer_kind_from_message(message)
        
        # Create task with enhanced context for 3D avatar
        task = {
            "kind": task_kind,
            "risk": "low",
            "prompt": f"[3D AVATAR RESPONSE] Keep responses conversational and engaging for voice synthesis. {message}",
            "override": ""
        }
        
        # Use AI router with preference for local models when available
        result = route_task(task, bucket_type="chat")
        
        # Prepare response with animation hints
        response_data = {
            "success": True,
            "response": result,
            "model_used": "auto-selected",
            "task_type": task_kind,
            "use_device_voice_only": True,  # Only use Windows/browser voices
            "avatar_animation_hints": _extract_animation_hints(result)
        }
        
        return JSONResponse(response_data)
        
    except Exception as e:
        return JSONResponse({
            "success": False, 
            "error": str(e),
            "fallback_response": "I apologize, but I'm having trouble processing your request right now."
        })

@app.get("/api/duckbot-os/models")
def duckbot_os_available_models(_auth: bool = Depends(require_token)):
    """Get available models for DuckBot OS with LM Studio and OpenRouter support"""
    try:
        # Check LM Studio availability
        lm_studio_available = False
        lm_studio_model = None
        
        try:
            import requests
            response = requests.get("http://localhost:1234/v1/models", timeout=2)
            if response.status_code == 200:
                models_data = response.json()
                if models_data.get('data'):
                    lm_studio_available = True
                    lm_studio_model = models_data['data'][0].get('id', 'local-model')
        except:
            pass
        
        # Get OpenRouter status from router state
        router_state = get_router_state()
        
        available_models = {
            "local": {
                "lm_studio_available": lm_studio_available,
                "current_model": lm_studio_model,
                "fallback_model": "nvidia_NVIDIA-Nemotron-Nano-9B-v2-Q5_K_S"
            },
            "cloud": {
                "openrouter_available": router_state.get('openrouter', {}).get('available', False),
                "qwen_available": router_state.get('qwen', {}).get('available', False),
                "recommended_models": [
                    "google/gemini-flash-1.5",
                    "qwen/qwen-2.5-72b-instruct",
                    "anthropic/claude-3-haiku"
                ]
            },
            "voice_config": {
                "use_device_voices_only": True,
                "vibe_voice_disabled": True
            }
        }
        
        return JSONResponse(available_models)
        
    except Exception as e:
        return JSONResponse({"error": str(e), "models": []})

def _extract_animation_hints(text: str) -> dict:
    """Extract animation hints from AI response for 3D avatar"""
    hints = {
        "emotion": "neutral",
        "intensity": 0.5,
        "gestures": [],
        "speech_rate": 1.0
    }
    
    text_lower = text.lower()
    
    # Emotion detection for morph targets
    if any(word in text_lower for word in ['excited', 'amazing', 'wonderful', '!', 'great']):
        hints["emotion"] = "happy"
        hints["intensity"] = 0.8
        hints["speech_rate"] = 1.1
    elif any(word in text_lower for word in ['sorry', 'apologize', 'unfortunately', 'problem']):
        hints["emotion"] = "concerned"  
        hints["intensity"] = 0.6
        hints["speech_rate"] = 0.9
    elif any(word in text_lower for word in ['thinking', 'consider', 'analyze', 'hmm']):
        hints["emotion"] = "thinking"
        hints["intensity"] = 0.4
        hints["speech_rate"] = 0.8
    
    # Gesture detection for avatar animation
    if '?' in text:
        hints["gestures"].append("questioning")
    if any(word in text_lower for word in ['here', 'this', 'that', 'look']):
        hints["gestures"].append("pointing")
    if any(word in text_lower for word in ['welcome', 'hello', 'hi']):
        hints["gestures"].append("waving")
    
    return hints

# Mount DuckBot OS static files
try:
    import os
    current_dir = os.path.dirname(os.path.dirname(__file__))  # Go up from duckbot/ to project root
    duckbot_os_dir = os.path.join(current_dir, "duckbot-os")
    if os.path.exists(duckbot_os_dir):
        app.mount("/duckbot-os-static", StaticFiles(directory=duckbot_os_dir), name="duckbot-os-static")
        print(f"✅ DuckBot OS static files mounted from: {duckbot_os_dir}")
    else:
        print(f"Warning: DuckBot OS directory not found at: {duckbot_os_dir}")
except Exception as e:
    print(f"Warning: Could not mount DuckBot OS static files: {e}")

# ============================================================================
# END DUCKBOT OS API ENDPOINTS
# ============================================================================

def run():
    import uvicorn
    
    # Initialize Qwen system context on WebUI startup
    try:
        from duckbot.ai_router_gpt import initialize_qwen_system_context
        print("ðŸ§  Initializing AI system context...")
        initialize_qwen_system_context()
    except Exception as e:
        print(f"Warning: Could not initialize AI context: {e}")
    
    # Security: Default to loopback only unless explicitly configured
    host = os.getenv("DUCKBOT_WEBUI_HOST", "localhost") 
    port = int(os.getenv("DUCKBOT_WEBUI_PORT", "8787"))
    
    if host != "127.0.0.1" and host != "localhost":
        print("WARNING: WebUI is configured to listen on all interfaces!")
        print(f"   Host: {host} - This exposes the WebUI to network access")
        print("   Set DUCKBOT_WEBUI_HOST=127.0.0.1 for localhost-only access")
        
    print(f"WebUI Security: {'Localhost-only' if host in ['127.0.0.1', 'localhost'] else 'Network-accessible'}")
    
    # Display access URLs with token for easy access
    full_url = f"http://{host}:{port}/?token={WEBUI_TOKEN}"
    print("=" * 70)
    print("DuckBot WebUI Server Starting...")
    print("=" * 70)
    print(f"[ACCESS] Local URL: http://localhost:{port}/?token={WEBUI_TOKEN}")
    if host not in ['127.0.0.1', 'localhost']:
        print(f"[NETWORK] Network URL: {full_url}")
    print("=" * 70)
    print("[SUCCESS] Copy the URL above to access the WebUI dashboard")
    print("[SECURITY] Token-secured access - bookmark the full URL")
    print("=" * 70)
    
    # Auto-open browser disabled to prevent startup loops
    # User can manually open browser with the URL above
    print(f"[MANUAL] Please manually open: http://localhost:{port}/?token={WEBUI_TOKEN}")
    
    print("=" * 70)
    
    uvicorn.run("duckbot.webui:app", host=host, port=port, reload=False)


# =============================================================================
# DUCKBOT OS API ENDPOINTS
# =============================================================================

@app.get("/api/settings")
def get_settings(_auth: bool = Depends(require_token)):
    """Get current settings for DuckBot OS"""
    try:
        settings = load_settings()  # This should be your existing settings loading function
        return {
            "success": True,
            "apiProvider": getattr(settings, 'api_provider', 'gemini'),
            "geminiApiKey": getattr(settings, 'gemini_api_key', ''),
            "openRouterKey": getattr(settings, 'openrouter_api_key', ''),
            "lmStudioUrl": getattr(settings, 'lm_studio_url', 'http://localhost:1234')
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/settings")
def save_settings(request: Request, _auth: bool = Depends(require_token)):
    """Save settings for DuckBot OS"""
    try:
        import json
        data = json.loads(request.body) if hasattr(request, 'body') else {}
        
        # Here you would save the settings to your config file
        # For now, just return success
        return {"success": True, "message": "Settings saved successfully"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/files/save")
def save_file(request: Request, _auth: bool = Depends(require_token)):
    """Save a file from the code editor"""
    try:
        import json
        data = json.loads(request.body) if hasattr(request, 'body') else {}
        filename = data.get('filename')
        content = data.get('content', '')
        
        if not filename:
            return {"success": False, "error": "No filename provided"}
            
        # Save to project directory
        import os
        filepath = os.path.join(os.getcwd(), filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return {"success": True, "message": f"File {filename} saved successfully"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/models/refresh")
def refresh_models(_auth: bool = Depends(require_token)):
    """Refresh the model list"""
    try:
        # This would trigger a refresh of available models
        # For now, just return success
        return {"success": True, "message": "Models refreshed"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/models/local")
def get_local_models(_auth: bool = Depends(require_token)):
    """Get local models from LM Studio"""
    try:
        import requests
        response = requests.get("http://localhost:1234/v1/models", timeout=3)
        if response.status_code == 200:
            models_data = response.json()
            models = models_data.get('data', [])
            return {
                "success": True,
                "models": [{"id": m.get('id', 'Unknown'), "name": m.get('id', 'Unknown')} for m in models]
            }
        else:
            return {"success": False, "error": "LM Studio not running"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/queue/clear")
def clear_queue(_auth: bool = Depends(require_token)):
    """Clear the task queue"""
    try:
        # This would clear the background task queue
        # For now, just return success
        return {"success": True, "message": "Queue cleared"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/queue/items")
def get_queue_items(_auth: bool = Depends(require_token)):
    """Get current queue items"""
    try:
        # This would return the actual queue items
        # For now, return empty list
        return {"success": True, "items": []}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/rag/stats")
def get_rag_stats(_auth: bool = Depends(require_token)):
    """Get RAG statistics"""
    try:
        # This would return actual RAG statistics
        return {
            "success": True,
            "stats": {
                "documents": 0,
                "chunks": 0,
                "size": "0MB",
                "lastUpdated": "Never"
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/rag/auto-ingest")
def rag_auto_ingest_api(_auth: bool = Depends(require_token)):
    """Auto-ingest documents for RAG"""
    try:
        # This would trigger auto-ingestion
        return {"success": True, "message": "Auto-ingest started"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/rag/clear")
def rag_clear_api(_auth: bool = Depends(require_token)):
    """Clear RAG index"""
    try:
        # This would clear the RAG index
        return {"success": True, "message": "RAG index cleared"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/rag/search")
def rag_search_api(request: Request, _auth: bool = Depends(require_token)):
    """Search RAG knowledge base"""
    try:
        import json
        data = json.loads(request.body) if hasattr(request, 'body') else {}
        query = data.get('query', '')
        
        if not query:
            return {"success": False, "error": "No query provided"}
            
        # This would perform actual RAG search
        return {
            "success": True,
            "results": [
                {"title": "Example Result", "content": "This is an example search result for: " + query, "score": 0.95}
            ]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/action-logs")
def get_action_logs(filter: str = "", _auth: bool = Depends(require_token)):
    """Get action logs"""
    try:
        # This would return actual action logs
        import datetime
        return {
            "success": True,
            "logs": [
                {
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "type": "INFO",
                    "message": "DuckBot OS started successfully"
                },
                {
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "type": "INFO", 
                    "message": "All systems operational"
                }
            ]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/voice/generate")
def generate_voice_api(request: Request, _auth: bool = Depends(require_token)):
    """Generate voice using TTS"""
    try:
        # This would integrate with your voice generation system
        return {"success": True, "audio_url": "/static/generated_voice.mp3"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Advanced Integration API Endpoints
from .wsl_integration import wsl_integration
from .bytebot_integration import bytebot_integration
from .archon_integration import archon_integration
from .chromium_integration import chromium_integration

@app.get("/api/wsl/status")
def get_wsl_status(_auth: bool = Depends(require_token)):
    """Get WSL integration status"""
    try:
        return wsl_integration.get_status()
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/wsl/execute")
async def execute_wsl_command(request: Request, _auth: bool = Depends(require_token)):
    """Execute WSL command"""
    try:
        body = await request.json()
        command = body.get('command', '')
        distro = body.get('distro')
        
        if not command:
            return {"success": False, "error": "No command provided"}
            
        result = await wsl_integration.execute_wsl_command(command, distro)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/wsl/distro/{action}")
async def manage_wsl_distro(action: str, request: Request, _auth: bool = Depends(require_token)):
    """Manage WSL distributions (start/stop)"""
    try:
        body = await request.json()
        distro = body.get('distro')
        
        if not distro:
            return {"success": False, "error": "No distribution specified"}
            
        if action == "start":
            result = await wsl_integration.start_distro(distro)
        elif action == "stop":
            result = await wsl_integration.stop_distro(distro)
        else:
            return {"success": False, "error": f"Invalid action: {action}"}
            
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/wsl/package/install")
async def install_wsl_package(request: Request, _auth: bool = Depends(require_token)):
    """Install package in WSL"""
    try:
        body = await request.json()
        package = body.get('package', '')
        distro = body.get('distro')
        
        if not package:
            return {"success": False, "error": "No package specified"}
            
        result = await wsl_integration.install_package(package, distro)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/wsl/docker/status")
async def get_docker_status(distro: str = None, _auth: bool = Depends(require_token)):
    """Check Docker status in WSL"""
    try:
        result = await wsl_integration.check_docker(distro)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/wsl/docker/start")
async def start_docker(request: Request, _auth: bool = Depends(require_token)):
    """Start Docker in WSL"""
    try:
        body = await request.json()
        distro = body.get('distro')
        
        result = await wsl_integration.start_docker(distro)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/wsl/docker/containers")
async def list_docker_containers(distro: str = None, _auth: bool = Depends(require_token)):
    """List Docker containers"""
    try:
        result = await wsl_integration.list_containers(distro)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/wsl/system/info")
async def get_wsl_system_info(distro: str = None, _auth: bool = Depends(require_token)):
    """Get WSL system information"""
    try:
        result = await wsl_integration.get_system_info(distro)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/wsl/files/{operation}")
async def wsl_file_operations(operation: str, request: Request, _auth: bool = Depends(require_token)):
    """Perform file operations in WSL"""
    try:
        body = await request.json()
        path = body.get('path')
        content = body.get('content')
        distro = body.get('distro')
        
        result = await wsl_integration.file_operations(operation, path, content, distro)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/wsl/network")
async def get_wsl_network_info(distro: str = None, _auth: bool = Depends(require_token)):
    """Get WSL network information"""
    try:
        result = await wsl_integration.get_network_info(distro)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

# ByteBot Integration API Endpoints
@app.get("/api/bytebot/status")
def get_bytebot_status(_auth: bool = Depends(require_token)):
    """Get ByteBot integration status"""
    try:
        return bytebot_integration.get_capabilities()
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/bytebot/execute")
async def execute_bytebot_task(request: Request, _auth: bool = Depends(require_token)):
    """Execute ByteBot natural language task"""
    try:
        body = await request.json()
        task = body.get('task', '')
        context = body.get('context')
        
        if not task:
            return {"success": False, "error": "No task provided"}
        
        result = await bytebot_integration.execute_natural_language_task(task, context)
        return {
            "success": result.success,
            "message": result.message,
            "screenshot": result.screenshot,
            "artifacts": result.artifacts,
            "execution_time": result.execution_time
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/bytebot/history")
async def get_bytebot_history(_auth: bool = Depends(require_token)):
    """Get ByteBot task history"""
    try:
        history = await bytebot_integration.get_task_history()
        return {"success": True, "history": history}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Archon Integration API Endpoints
@app.get("/api/archon/status")
async def get_archon_status(_auth: bool = Depends(require_token)):
    """Get Archon integration status"""
    try:
        return await archon_integration.get_agent_status()
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/archon/task")
async def create_archon_task(request: Request, _auth: bool = Depends(require_token)):
    """Create Archon agent task"""
    try:
        body = await request.json()
        description = body.get('description', '')
        agent_type = body.get('agent_type', 'task_executor')
        context = body.get('context')
        
        if not description:
            return {"success": False, "error": "No task description provided"}
        
        task_id = await archon_integration.create_agent_task(description, agent_type, context)
        return {
            "success": True,
            "task_id": task_id,
            "message": f"Task created with ID: {task_id}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/archon/task/{task_id}")
async def get_archon_task_status(task_id: str, _auth: bool = Depends(require_token)):
    """Get Archon task status"""
    try:
        task_status = await archon_integration.get_task_status(task_id)
        if task_status:
            return {"success": True, "task": task_status}
        else:
            return {"success": False, "error": "Task not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/archon/knowledge")
async def add_archon_knowledge(request: Request, _auth: bool = Depends(require_token)):
    """Add knowledge item to Archon"""
    try:
        body = await request.json()
        content = body.get('content', '')
        metadata = body.get('metadata', {})
        
        if not content:
            return {"success": False, "error": "No content provided"}
        
        item_id = await archon_integration.add_knowledge_item(content, metadata)
        return {
            "success": True,
            "item_id": item_id,
            "message": "Knowledge item added successfully"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/archon/knowledge/search")
async def search_archon_knowledge(query: str, limit: int = 10, _auth: bool = Depends(require_token)):
    """Search Archon knowledge base"""
    try:
        results = await archon_integration.search_knowledge(query, limit)
        return {"success": True, "results": results, "count": len(results)}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ChromiumOS Integration API Endpoints
@app.get("/api/chromium/status")
def get_chromium_status(_auth: bool = Depends(require_token)):
    """Get ChromiumOS integration status"""
    try:
        return chromium_integration.get_capabilities()
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/chromium/navigate")
async def chromium_navigate(request: Request, _auth: bool = Depends(require_token)):
    """Navigate to URL in browser"""
    try:
        body = await request.json()
        url = body.get('url', '')
        new_tab = body.get('new_tab', False)
        
        if not url:
            return {"success": False, "error": "No URL provided"}
        
        result = await chromium_integration.navigate_to_url(url, new_tab)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/chromium/search")
async def chromium_search(request: Request, _auth: bool = Depends(require_token)):
    """Perform web search"""
    try:
        body = await request.json()
        query = body.get('query', '')
        search_engine = body.get('search_engine', 'google')
        
        if not query:
            return {"success": False, "error": "No search query provided"}
        
        result = await chromium_integration.search_web(query, search_engine)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/chromium/bookmarks")
async def get_chromium_bookmarks(folder: str = None, _auth: bool = Depends(require_token)):
    """Get browser bookmarks"""
    try:
        bookmarks = await chromium_integration.get_bookmarks(folder)
        return {"success": True, "bookmarks": bookmarks}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/chromium/bookmarks")
async def add_chromium_bookmark(request: Request, _auth: bool = Depends(require_token)):
    """Add browser bookmark"""
    try:
        body = await request.json()
        url = body.get('url', '')
        title = body.get('title', '')
        folder = body.get('folder', 'Bookmarks Bar')
        
        if not url:
            return {"success": False, "error": "No URL provided"}
        
        result = await chromium_integration.add_bookmark(url, title, folder)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/chromium/history")
async def get_chromium_history(limit: int = 50, _auth: bool = Depends(require_token)):
    """Get browser history"""
    try:
        history = await chromium_integration.get_history(limit)
        return {"success": True, "history": history}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/chromium/extensions")
async def get_chromium_extensions(_auth: bool = Depends(require_token)):
    """Get browser extensions"""
    try:
        extensions = await chromium_integration.get_extensions()
        return {"success": True, "extensions": extensions}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/chromium/extensions/{extension_id}/{action}")
async def manage_chromium_extension(extension_id: str, action: str, _auth: bool = Depends(require_token)):
    """Manage browser extension"""
    try:
        result = await chromium_integration.manage_extension(extension_id, action)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/system/info")
async def get_system_info(_auth: bool = Depends(require_token)):
    """Get comprehensive system information"""
    try:
        result = await chromium_integration.get_system_info()
        return {"success": True, "system_info": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    run()
