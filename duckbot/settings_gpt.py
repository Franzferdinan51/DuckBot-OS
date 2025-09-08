
# duckbot/settings_gpt.py
"""
Runtime settings for AI System Manager (local-first router).
Values are persisted to JSON, then applied to environment at startup via sitecustomize.py.
This keeps n8n flows untouched while letting operators tweak manager behavior.
"""
import os, json, time, threading
from pathlib import Path

DEFAULTS = {
    # Routing and model selection
    "AI_ROUTING_MODE": "cloud_first",              # cloud_first or local_first
    "AI_MODEL_MAIN_BRAIN": "qwen/qwen3-coder:free",# OpenRouter primary brain
    "LM_STUDIO_MODEL": "qwen/qwen3-coder-30b",     # Preferred local model (if available)
    # WebUI chat behavior
    "FORCE_CLOUD_FOR_CHAT": "0",                   # 1 to always try cloud on /chat

    # Local tuning
    "AI_LOCAL_STRICT": "1",
    "AI_LOCAL_MAX_ATTEMPTS": "2",
    "AI_LOCAL_CONF_MIN": "0.68",

    # Cloud budget and routing limits
    "OPENROUTER_BUDGET_PER_MIN": "6",
    "AI_TTL_CACHE_SEC": "60",
    "AI_MAX_HOPS_ROUTINE": "1",
    "AI_MAX_HOPS_CRITICAL": "3",
    "AI_CONFIDENCE_MIN": "0.75",

    # Cloud model selection (user-swappable)
    "AI_MODEL_MAIN_BRAIN": "qwen/qwen3-coder:free",
    "AI_MODEL_CODE": "qwen/qwen3-coder:free",
    "AI_MODEL_ANALYSIS": "glm/glm-4.5-air:free",
    "AI_MODEL_DEBUG": "qwen/qwen3-coder:free",
    "AI_MODEL_SERVER_BRAIN": "qwen/qwen3-coder:free",

    # Reasoning model (QwQ) toggle + id
    "ENABLE_QWQ_REASONING": "0",
    "AI_MODEL_REASONING": "qwen/qwq-32b:free",

    # OpenRouter tier environment overrides used by the router
    "OR_QWEN_CODER": "qwen/qwen3-coder:free",
    "OR_GLM_AIR": "z-ai/glm-4.5-air:free",
    "OR_NEMO": "qwen/qwen3-coder:free",
    "OR_KIMI": "moonshot/kimi-k2:free",
    "OR_R1": "deepseek/deepseek-r1:free",
    "OR_QWQ": "qwen/qwq-32b:free",

    # Toggle to use paid variants of same models (strip :free suffix)
    "USE_PAID_MODEL_VARIANTS": "0",

    # Retrieval-Augmented Generation (RAG)
    "RAG_ENABLED": "1",
    "RAG_TOP_K": "4",
    "RAG_MAX_CONTEXT_CHARS": "2000",
    # Comma-separated kinds or * to apply to all
    "RAG_INCLUDE_KINDS": "status,summary,code,json_format,long_form,*,reasoning",
}

SETTINGS_PATH = Path(os.getenv("DUCKBOT_SETTINGS_PATH", "duckbot/ai_manager_settings.json"))
settings_lock = threading.RLock()
_settings_cache = None
_settings_cache_time = 0
CACHE_TTL = 5  # seconds

def atomic_write_settings(file_path: Path, data):
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

def load_settings(use_cache=True):
    global _settings_cache, _settings_cache_time
    
    with settings_lock:
        # Return cached if recent and requested
        if use_cache and _settings_cache and (time.time() - _settings_cache_time) < CACHE_TTL:
            return _settings_cache.copy()
            
        data = {}
        if SETTINGS_PATH.exists():
            try:
                data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            except Exception as e:
                # Log corruption but don't crash
                print(f"Warning: Settings file corrupted, using defaults: {e}")
                data = {}
                
        # Start with defaults, then overlay saved, then overlay process env (env wins)
        combined = DEFAULTS.copy()
        combined.update(data or {})
        for k in list(DEFAULTS.keys()):
            if k in os.environ and os.environ[k]:
                combined[k] = os.environ[k]
                
        # Cache the result
        _settings_cache = combined.copy()
        _settings_cache_time = time.time()
        return combined

def save_settings(values: dict):
    global _settings_cache, _settings_cache_time
    
    with settings_lock:
        # Only persist known keys as strings
        clean = {k: str(values.get(k, DEFAULTS[k])) for k in DEFAULTS}
        
        try:
            SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
            atomic_write_settings(SETTINGS_PATH, clean)
            
            # Update cache
            _settings_cache = clean.copy()
            _settings_cache_time = time.time()
            
            return clean
        except Exception as e:
            print(f"Error saving settings: {e}")
            # Return what we tried to save even if write failed
            return clean

def apply_to_env(values=None):
    values = values or load_settings()
    for k,v in values.items():
        os.environ[k] = str(v)
    return values
