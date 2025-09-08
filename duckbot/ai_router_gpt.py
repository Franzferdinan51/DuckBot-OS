# ai_router_gpt.py (Cloud-First default with Local fallback)
import os, time, hashlib, requests, logging, traceback, threading
from collections import deque
from pathlib import Path
from dotenv import load_dotenv
from duckbot.rag import maybe_augment_with_rag, index_stats, auto_ingest_defaults

# Load environment variables
load_dotenv()

# Setup logging for router exceptions
logging.basicConfig(level=logging.ERROR)
router_logger = logging.getLogger("duckbot.router")

# Agent Pause State
AGENT_PAUSED = False
_agent_lock = threading.Lock()

def pause_agent():
    global AGENT_PAUSED
    with _agent_lock:
        AGENT_PAUSED = True

def resume_agent():
    global AGENT_PAUSED
    with _agent_lock:
        AGENT_PAUSED = False

# Import action and reasoning logger
try:
    from duckbot.action_reasoning_logger import action_logger
    ACTION_LOGGING_AVAILABLE = True
except ImportError:
    ACTION_LOGGING_AVAILABLE = False
    router_logger.warning("Action reasoning logger not available")

# Import dynamic model manager for advanced local model handling
try:
    from duckbot.dynamic_model_manager import DynamicModelManager
    DYNAMIC_MODEL_MANAGER = DynamicModelManager()
    DYNAMIC_LOADING_AVAILABLE = True
except ImportError:
    DYNAMIC_LOADING_AVAILABLE = False
    router_logger.warning("Dynamic model manager not available - using basic model selection")

# Import local feature parity for full cloud feature equivalence
try:
    from duckbot.local_feature_parity import ensure_full_local_parity, local_parity
    LOCAL_PARITY_AVAILABLE = True
except ImportError:
    LOCAL_PARITY_AVAILABLE = False
    router_logger.warning("Local feature parity not available - some features may be limited in local mode")

# System initialization flag
_SYSTEM_INITIALIZED = False

# Enhanced AI capabilities
try:
    from duckbot.qwen_agent_integration import is_qwen_agent_available, execute_enhanced_task
    ENHANCED_AI_AVAILABLE = True
except ImportError:
    ENHANCED_AI_AVAILABLE = False
    router_logger.warning("Qwen-Agent integration not available - using basic AI routing")

# Enhanced Provider Connectors
try:
    from duckbot.provider_connectors import (
        connector_manager, complete_chat, stream_chat, switch_provider, 
        get_provider_status, get_available_providers
    )
    ENHANCED_CONNECTORS_AVAILABLE = True
except ImportError:
    ENHANCED_CONNECTORS_AVAILABLE = False
    router_logger.warning("Enhanced provider connectors not available")

# Intelligent Agents
try:
    from duckbot.intelligent_agents import (
        analyze_with_intelligence, collaborative_intelligence,
        get_agent_performance, train_agent, AgentType, AgentContext
    )
    INTELLIGENT_AGENTS_AVAILABLE = True
except ImportError:
    INTELLIGENT_AGENTS_AVAILABLE = False
    router_logger.warning("Intelligent agents not available")

# Context Management
try:
    from duckbot.context_manager import (
        create_context, find_patterns, learn_from_experience,
        store_memory, get_memory, get_insights
    )
    CONTEXT_MANAGEMENT_AVAILABLE = True
except ImportError:
    CONTEXT_MANAGEMENT_AVAILABLE = False
    router_logger.warning("Context management not available")

# Claude Code integration (legacy support)
try:
    from duckbot.claude_code_integration import (
        initialize_claude_code, execute_claude_code_task, 
        is_claude_code_available, get_claude_code_status
    )
    CLAUDE_CODE_AVAILABLE = True
except ImportError:
    CLAUDE_CODE_AVAILABLE = False
    router_logger.warning("Claude Code integration not available - using basic code tools")

def _get_available_models():
    """Get list of currently available models for action logging"""
    models = []
    
    # Enhanced connectors
    if ENHANCED_CONNECTORS_AVAILABLE:
        try:
            providers = get_available_providers()
            for provider in providers:
                provider_status = get_provider_status().get(provider, {})
                if provider_status.get("connected"):
                    models.extend(provider_status.get("models", [provider]))
        except Exception as e:
            router_logger.error(f"Error getting enhanced models: {e}")
    
    # Legacy models
    if ROUTING_MODE == "cloud_first":
        models.extend(["qwen", "glm-4.5-air-prod"])
    models.extend(["local"])
    
    # Add any force-available models
    try:
        lm_model = get_lm_studio_model()
        if lm_model:
            models.append(f"local:{lm_model}")
    except:
        pass
    
    # Add Claude Code models if available
    if CLAUDE_CODE_AVAILABLE:
        try:
            from duckbot.claude_code_integration import claude_code_integration
            claude_models = claude_code_integration.get_available_models()
            models.extend([f"claude:{model}" for model in claude_models])
        except:
            pass
    
    return models

def can_use_claude_code_tools(task):
    """Check if task can benefit from Claude Code tools integration"""
    if not CLAUDE_CODE_AVAILABLE:
        return False
    
    kind = task.get("kind", "*")
    content = str(task.get("content", "")).lower()
    
    # Code-related tasks that benefit from Claude Code
    code_indicators = [
        "debug", "fix", "analyze", "review", "refactor", "optimize",
        "code", "function", "class", "import", "error", "bug",
        "syntax", "logic", "performance", "test", "unit test",
        "integration", "api", "endpoint", "database", "query",
        "algorithm", "data structure", "architecture", "design pattern"
    ]
    
    # Check if task involves code work
    return (
        kind in ["code", "debug", "analyze", "review"] or
        any(indicator in content for indicator in code_indicators) or
        any(ext in content for ext in [".py", ".js", ".ts", ".java", ".cpp", ".go", ".rs"])
    )

def can_use_qwen_code_tools(task):
    """Check if task can benefit from Qwen Code tools integration"""
    kind = task.get("kind", "*")
    prompt = task.get("prompt", "").lower()
    
    # Tasks that benefit from Qwen Code tools
    code_indicators = [
        kind in ("code", "json_format", "debugging", "analysis"),
        any(keyword in prompt for keyword in ["code", "function", "debug", "analyze", "review", "refactor", "test", "documentation"]),
        any(lang in prompt for lang in ["python", "javascript", "typescript", "java", "c++", "rust", "go"]),
        ".py" in prompt or ".js" in prompt or ".ts" in prompt or ".java" in prompt
    ]
    
    return any(code_indicators)

def initialize_qwen_system_context(local_only=False):
    """Send system context to Qwen model on startup"""
    global _SYSTEM_INITIALIZED
    
    if _SYSTEM_INITIALIZED:
        return
    
    # Set routing mode based on local_only flag
    if local_only:
        os.environ['AI_LOCAL_ONLY_MODE'] = 'true'
        os.environ['DISABLE_OPENROUTER'] = 'true'
        os.environ['ENABLE_LM_STUDIO_ONLY'] = 'true'
        print("[LOCAL] Local-only mode enabled - using only loaded LM Studio models")
    
    try:
        # Load system prompt
        base_dir = Path(__file__).parent.parent
        prompt_file = base_dir / "qwen_system_prompt.md"
        
        if not prompt_file.exists():
            router_logger.warning("Qwen system prompt not found")
            return
            
        with open(prompt_file, 'r', encoding='utf-8') as f:
            system_prompt = f.read()
        
        # Send initialization prompt to Qwen
        init_task = {
            "kind": "system_init",
            "risk": "low",
            "prompt": (
                "SYSTEM INITIALIZATION (concise):\n"
                + system_prompt[:2000]
                + "\n\nACK: Reply exactly: 'DuckBot AI Brain ready.'"
            ),
            "model": "qwen/qwen3-coder:free",
            "override": "lower_conf:0.50"
        }
        
        router_logger.info("Initializing Qwen system context...")
        response = route_task(init_task, bucket_type="background")
        
        text_ok = (response or {}).get("response", "") or (response or {}).get("text", "")
        if text_ok and ("ready" in text_ok.lower() or "initialized" in text_ok.lower()):
            router_logger.info("[OK] Qwen system context initialized successfully")
        else:
            router_logger.warning("[WARNING] Qwen system context initialization may have failed")
        
        # Initialize Claude Code integration if available
        try:
            if CLAUDE_CODE_AVAILABLE:
                import asyncio
                loop = None
                try:
                    loop = asyncio.get_event_loop()
                    if not loop.is_running():
                        claude_init_success = asyncio.run(initialize_claude_code())
                    else:
                        # Skip async init in running loop context
                        claude_init_success = False
                except:
                    claude_init_success = False
                
                if claude_init_success:
                    router_logger.info("[OK] Claude Code integration initialized successfully")
                else:
                    router_logger.warning("[WARNING] Claude Code integration initialization failed")
            else:
                router_logger.info("[INFO] Claude Code integration not available - skipping")
        except Exception as claude_e:
            router_logger.warning(f"[WARNING] Claude Code initialization error: {claude_e}")
        
        _SYSTEM_INITIALIZED = True
            
    except Exception as e:
        router_logger.error(f"Failed to initialize Qwen system context: {e}")
        
def ensure_system_initialized():
    """Ensure system is initialized before processing tasks"""
    if not _SYSTEM_INITIALIZED:
        initialize_qwen_system_context()

def handle_server_management_task(task):
    """AI-powered server management using Qwen intelligence"""
    prompt = task.get("prompt", "").lower()
    
    # Detect server management intent using broader keywords
    server_indicators = ["server", "service", "ecosystem", "comfyui", "webui", "lmstudio", "jupyter", "n8n", "start", "stop", "restart", "status", "launch", "shutdown", "running", "check"]
    
    if any(indicator in prompt for indicator in server_indicators):
        return _qwen_server_management(task)
    
    return None

def _qwen_server_management(task):
    """Qwen AI-powered intelligent server management"""
    try:
        from duckbot.server_manager import server_manager
        
        # Get current server state for AI context
        status = server_manager.get_all_service_status()
        status_context = []
        for name, info in status.items():
            port_info = f" (port {info.port})" if info.port else ""
            status_context.append(f"{info.display_name}{port_info}: {info.status.value}")
        
        current_status = "Current server status:\n" + "\n".join(status_context)
        
        # Create AI prompt with server context
        ai_prompt = f"""You are DuckBot's AI Server Manager. Analyze this request and provide intelligent server management.

{current_status}

Available services: ComfyUI (image generation), WebUI (dashboard), LM Studio (local AI), Jupyter (notebooks), n8n (automation), Open Notebook (AI notebooks)

User request: "{task.get('prompt', '')}"

Respond with:
1. Your analysis of what the user wants
2. The specific action to take (start/stop/restart/status/analysis)
3. Which service(s) to target (or "ecosystem" for all)
4. Any recommendations or warnings

Format your response as natural language that explains your reasoning and the action taken."""

        # Route to Qwen for intelligent decision making
        ai_task = {
            "kind": "server_management",
            "risk": "low", 
            "prompt": ai_prompt,
            "override": f"force:{os.getenv('AI_MODEL_SERVER_BRAIN', 'qwen/qwen3-coder:free')}"
        }
        
        # Get AI analysis and decision
        ai_response = _call_tier("qwen", ai_prompt, ai_task)
        
        if ai_response and not ai_response.get("failure"):
            ai_analysis = ai_response.get("text", "")
            
            # Extract action from AI response and execute
            execution_result = _execute_ai_server_decision(ai_analysis, task, status)
            
            # Combine AI reasoning with execution result
            return {
                "text": f"[BRAIN] **AI Server Manager Analysis:**\n{ai_analysis}\n\n[METRICS] **Execution Result:**\n{execution_result.get('text', 'Action completed')}",
                "confidence": max(ai_response.get("confidence", 0.8), execution_result.get("confidence", 0.8)),
                "model_used": f"qwen-server-manager ({ai_response.get('model_used', 'qwen')})",
                "ai_analysis": ai_analysis,
                "execution_result": execution_result,
                "success": execution_result.get("success", True)
            }
        else:
            # Fallback to basic server management if AI fails
            return _basic_server_fallback(task, status)
            
    except Exception as e:
        return {
            "text": f"[EMOJI] AI Server Manager error: {str(e)}\nFalling back to basic server management.",
            "confidence": 0.6,
            "model_used": "qwen-server-manager-error",
            "error": True
        }

def _execute_ai_server_decision(ai_analysis: str, task: dict, current_status: dict):
    """Execute server actions based on AI analysis"""
    try:
        from duckbot.server_manager import server_manager
        
        analysis_lower = ai_analysis.lower()
        prompt_lower = task.get('prompt', '').lower()
        
        # Extract services mentioned
        services = ["lm_studio", "comfyui", "webui", "n8n", "open_notebook", "jupyter", "discord_bot"]
        target_services = []
        
        for service in services:
            if service.replace("_", " ") in analysis_lower or service in analysis_lower or service.replace("_", " ") in prompt_lower:
                target_services.append(service)
        
        # Determine action from AI analysis
        if any(word in analysis_lower for word in ["start", "launch", "run", "boot", "initialize"]):
            if "ecosystem" in analysis_lower or len(target_services) > 2:
                success, results = server_manager.start_ecosystem()
                message = f"[START] Started ecosystem services\n" + "\n".join(results)
            elif target_services:
                results = []
                for service in target_services:
                    success, msg = server_manager.start_service(service)
                    results.append(f"• {service}: {msg}")
                message = "[START] Service startup results:\n" + "\n".join(results)
                success = all("success" in result.lower() for result in results)
            else:
                return {"text": "[EMOJI] AI analysis didn't specify which service to start", "confidence": 0.7}
                
        elif any(word in analysis_lower for word in ["stop", "shutdown", "kill", "terminate", "halt"]):
            if "ecosystem" in analysis_lower or len(target_services) > 2:
                success, results = server_manager.stop_ecosystem()
                message = f"[STOP] Stopped ecosystem services\n" + "\n".join(results)
            elif target_services:
                results = []
                for service in target_services:
                    success, msg = server_manager.stop_service(service)
                    results.append(f"• {service}: {msg}")
                message = "[STOP] Service shutdown results:\n" + "\n".join(results)
                success = all("success" in result.lower() for result in results)
            else:
                return {"text": "[EMOJI] AI analysis didn't specify which service to stop", "confidence": 0.7}
                
        elif any(word in analysis_lower for word in ["restart", "reboot", "reload"]):
            if target_services:
                results = []
                for service in target_services:
                    success, msg = server_manager.restart_service(service)
                    results.append(f"• {service}: {msg}")
                message = "[LOADING] Service restart results:\n" + "\n".join(results)
                success = all("success" in result.lower() for result in results)
            else:
                return {"text": "[EMOJI] AI analysis didn't specify which service to restart", "confidence": 0.7}
                
        else:
            # Status check or analysis only
            return {"text": "[METRICS] Status analysis completed", "confidence": 0.9, "success": True}
        
        return {
            "text": message,
            "confidence": 0.95,
            "success": success
        }
        
    except Exception as e:
        return {
            "text": f"[WARNING] Execution error: {str(e)}",
            "confidence": 0.6,
            "success": False
        }

def _basic_server_fallback(task: dict, current_status: dict):
    """Basic server management fallback when AI is unavailable"""
    prompt = task.get("prompt", "").lower()
    
    # Simple keyword matching as fallback
    if any(word in prompt for word in ["start", "launch", "run"]):
        action = "[START] Would start services (AI unavailable, please specify which service)"
    elif any(word in prompt for word in ["stop", "shutdown", "halt"]):
        action = "[STOP] Would stop services (AI unavailable, please specify which service)"  
    elif any(word in prompt for word in ["restart", "reboot"]):
        action = "[LOADING] Would restart services (AI unavailable, please specify which service)"
    else:
        # Status display
        status_lines = []
        for name, info in current_status.items():
            port_info = f" (port {info.port})" if info.port else ""
            status_lines.append(f"• {info.display_name}{port_info}: {info.status.value}")
        action = "[METRICS] Current Status:\n" + "\n".join(status_lines)
    
    return {
        "text": f"[EMOJI] **Fallback Server Manager:**\n{action}",
        "confidence": 0.7,
        "model_used": "basic-server-fallback",
        "success": True
    }

def _select_best_available_model(available_models, task=None):
    """Select the best model from actually available loaded models in LM Studio"""
    if not available_models:
        return None
    
    # If only one model available, use it
    if len(available_models) == 1:
        return available_models[0]
    
    # Model preference ranking based on capabilities
    model_rankings = {
        # Highest priority: Newest and most capable models
        "bartowski/nvidia-llama-3.3-nemotron": 100,  # Best reasoning
        "nemotron": 95,
        "llama-3.3": 90,
        
        # High priority: Latest Qwen models
        "qwen3-coder-30b": 85,
        "qwen/qwen3-coder": 85,
        "qwen3": 80,
        "qwen2.5-coder": 75,
        "qwq": 70,
        
        # Medium priority: General purpose models
        "gpt-oss-120b": 65,
        "gpt-oss-20b": 60,
        "gemma-3-27b": 55,
        
        # Lower priority: Smaller/older models
        "gemma-3-12b": 45,
        "devstral": 40,
        "gemma": 35,
    }
    
    # Task-specific preferences
    task_preferences = {}
    if task:
        kind = task.get("kind", "*")
        prompt_length = len(task.get("prompt", ""))
        risk = task.get("risk", "low")
        
        if kind in ("reasoning", "policy", "arbiter") or risk in ("medium", "high"):
            # Prefer larger reasoning models
            task_preferences["nemotron"] = 20
            task_preferences["qwen3"] = 15
        elif kind in ("code", "json_format", "debugging"):
            # Prefer coding models
            task_preferences["coder"] = 25
            task_preferences["qwen"] = 15
        elif prompt_length < 100:
            # Prefer smaller efficient models for short prompts
            task_preferences["gemma-3-12b"] = 20
            task_preferences["gemma"] = 15
        elif prompt_length > 2000:
            # Prefer largest available models
            task_preferences["120b"] = 25
            task_preferences["nemotron"] = 20
    
    # Score each available model
    best_model = available_models[0]
    best_score = 0
    
    for model in available_models:
        score = 1  # Base score
        model_lower = model.lower()
        
        # Add ranking points
        for pattern, points in model_rankings.items():
            if pattern in model_lower:
                score += points
                break
        
        # Add task-specific bonus
        for pattern, bonus in task_preferences.items():
            if pattern in model_lower:
                score += bonus
        
        if score > best_score:
            best_score = score
            best_model = model
    
    router_logger.info(f"Selected '{best_model}' (score: {best_score}) from available models")
    return best_model

def get_optimal_model_for_task(task):
    """Select the best local model based on task requirements and system resources"""
    kind = task.get("kind", "*")
    prompt = task.get("prompt", "")
    risk = task.get("risk", "low")
    
    # Check if Qwen Code tools can enhance this task
    use_qwen_tools = can_use_qwen_code_tools(task)
    
    # Model selection logic based on your actual available models (configurable via .env)
    model_preferences = {
        # Code tasks - Use Qwen Coder models (excellent for programming)
        "code": os.getenv("AI_MODEL_CODE", "qwen/qwen3-coder-30b"),
        "json_format": os.getenv("AI_MODEL_JSON", "qwen/qwen3-coder-30b"), 
        "debugging": os.getenv("AI_MODEL_DEBUG", "qwen/qwen2.5-coder-32b"),
        "analysis": os.getenv("AI_MODEL_ANALYSIS", "qwen/qwen3-coder-30b"),
        
        # Complex reasoning - Use larger models for better capability  
        "reasoning": os.getenv("AI_MODEL_REASONING", "bartowski/nvidia-llama-3.3-nemotron-super-49b-v1.5-gguf-q4-k-l"),
        "policy": os.getenv("AI_MODEL_POLICY", "bartowski/nvidia-llama-3.3-nemotron-super-49b-v1.5-gguf-q4-k-l"),
        "arbiter": os.getenv("AI_MODEL_ARBITER", "bartowski/nvidia-llama-3.3-nemotron-super-49b-v1.5-gguf-q4-k-l"),
        "long_form": os.getenv("AI_MODEL_LONG_FORM", "bartowski/nvidia-llama-3.3-nemotron-super-49b-v1.5-gguf-q4-k-l"),
        
        # Server management tasks - Use server brain
        "server_start": os.getenv("AI_MODEL_SERVER_BRAIN", "qwen/qwen3-coder:free"),
        "server_stop": os.getenv("AI_MODEL_SERVER_BRAIN", "qwen/qwen3-coder:free"), 
        "server_management": os.getenv("AI_MODEL_SERVER_BRAIN", "qwen/qwen3-coder:free"),
        
        # Quick status/summary - Use efficient smaller models
        "status": os.getenv("AI_MODEL_STATUS", "google/gemma-3-12b"),
        "summary": os.getenv("AI_MODEL_SUMMARY", "google/gemma-3-12b"),
        
        # Question answering - Use QwQ specialist
        "qa": os.getenv("AI_MODEL_QA", "qwen/qwq-32b"),
        "question": os.getenv("AI_MODEL_QUESTION", "qwen/qwq-32b"),
        
        # Development tasks - Use Devstral
        "development": os.getenv("AI_MODEL_DEVELOPMENT", "mistralai/devstral-small-2507"),
        
        # Server management - Use main brain Qwen3 Coder Free (configurable)
        "server_start": os.getenv("AI_MODEL_SERVER_BRAIN", "qwen/qwen3-coder:free"),
        "server_stop": os.getenv("AI_MODEL_SERVER_BRAIN", "qwen/qwen3-coder:free"), 
        "server_status": os.getenv("AI_MODEL_SERVER_BRAIN", "qwen/qwen3-coder:free"),
        "server_restart": os.getenv("AI_MODEL_SERVER_BRAIN", "qwen/qwen3-coder:free"),
        "service_management": os.getenv("AI_MODEL_SERVER_BRAIN", "qwen/qwen3-coder:free"),
        "ecosystem_management": os.getenv("AI_MODEL_SERVER_BRAIN", "qwen/qwen3-coder:free"),
        
        # Default for unknown tasks - Use main brain (configurable)
        "*": os.getenv("AI_MODEL_MAIN_BRAIN", "qwen/qwen3-coder:free")
    }
    
    # Resource-conscious overrides based on system load
    prompt_length = len(prompt)
    
    # For very short prompts, use smaller efficient models (unless code-related)
    if prompt_length < 100 and not use_qwen_tools:
        return "google/gemma-3-12b"
    
    # For very long prompts (>2000 chars), use the largest capable model
    if prompt_length > 2000:
        return os.getenv("AI_MODEL_LARGE", "bartowski/nvidia-llama-3.3-nemotron-super-49b-v1.5-gguf-q4-k-l")  # Powerful 49B model
    
    # For high-risk or reasoning tasks, use robust models
    if risk in ("medium", "high") or kind == "reasoning":
        return os.getenv("AI_MODEL_REASONING", "bartowski/nvidia-llama-3.3-nemotron-super-49b-v1.5-gguf-q4-k-l")  # Nemotron for complex tasks
    
    # Use task-specific preference or default to Qwen Coder
    selected_model = model_preferences.get(kind, model_preferences["*"])
    
    # Log when Qwen Code tools integration is beneficial
    if use_qwen_tools:
        router_logger.info(f"Task benefits from Qwen Code tools integration: {kind}")
    
    return selected_model

def get_local_only_model_for_task(task):
    """Select best available loaded model for task in local-only mode with dynamic loading"""
    # Use advanced dynamic model manager if available
    if DYNAMIC_LOADING_AVAILABLE and os.getenv('ENABLE_DYNAMIC_LOADING') == 'true':
        try:
            return DYNAMIC_MODEL_MANAGER.get_or_load_model_for_task(task)
        except Exception as e:
            router_logger.warning(f"Dynamic model manager failed: {e}, falling back to basic selection")
    
    # Fallback to basic selection from already loaded models
    available_models = get_available_local_models()
    if not available_models:
        return "No model loaded"
    
    # Use the existing smart selection logic but only from loaded models
    available_ids = [m["id"] for m in available_models]
    selected = _select_best_available_model(available_ids, task)
    
    if selected:
        task_kind = task.get("kind", "*") if task else "*"
        print(f"[FOCUS] Local-only: Selected '{selected}' for task type '{task_kind}'")
        return selected
    
    # Fallback to first available
    return available_ids[0] if available_ids else "No model loaded"

def get_lm_studio_model(task=None):
    """Dynamically detect or select optimal model in LM Studio"""
    global _lm_studio_model_cache, _lm_studio_model_cache_time
    
    # Check for local-only mode first
    if os.getenv('AI_LOCAL_ONLY_MODE') == 'true':
        return get_local_only_model_for_task(task)
    
    # FIXED: Use thread-safe cache access
    with _cache_lock:
        current_time = time.time()
        # Cache for 60 seconds to avoid excessive API calls
        if _lm_studio_model_cache and (current_time - _lm_studio_model_cache_time) < 60:
            return _lm_studio_model_cache
    
    try:
        # Try to get the list of loaded models from LM Studio
        router_logger.debug(f"Checking LM Studio models at {LM_STUDIO_URL}/models")
        response = requests.get(f"{LM_STUDIO_URL}/models", timeout=5)
        
        if response.status_code == 200:
            models = response.json()
            router_logger.debug(f"LM Studio response: {models}")
            
            if models.get("data") and len(models["data"]) > 0:
                # Dynamically select the best available model for the task
                available_models = [m["id"] for m in models["data"]]
                router_logger.info(f"[OK] LM Studio models available: {available_models}")
                
                # Select optimal model based on task and available models
                model_id = _select_best_available_model(available_models, task)
                
                # FIXED: Thread-safe cache update
                with _cache_lock:
                    _lm_studio_model_cache = model_id
                    _lm_studio_model_cache_time = current_time
                router_logger.info(f"[FOCUS] Selected LM Studio model: {model_id}")
                return model_id
            else:
                router_logger.warning("[WARNING] LM Studio responded but no models loaded")
        else:
            router_logger.warning(f"[WARNING] LM Studio API returned status {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        router_logger.debug("[EMOJI] LM Studio not running or not accessible")
    except requests.exceptions.Timeout:
        router_logger.warning("⏱️ LM Studio API timeout - server may be busy")
    except Exception as e:
        # Use basic string conversion since sanitize_for_logging is defined later
        router_logger.warning(f"Could not detect LM Studio model: {str(e)[:100]}")
    
    # Smart fallback: choose optimal model for task if provided
    if task:
        optimal_model = get_optimal_model_for_task(task)
        router_logger.info(f"Selected optimal model for task '{task.get('kind', '*')}': {optimal_model}")
        with _cache_lock:
            _lm_studio_model_cache = optimal_model
            _lm_studio_model_cache_time = current_time
        return optimal_model
    
    # Environment override or indicate no local model available
    fallback = os.getenv("LM_STUDIO_MODEL", "No model loaded")
    
    # FIXED: Thread-safe fallback cache update
    with _cache_lock:
        _lm_studio_model_cache = fallback
        _lm_studio_model_cache_time = current_time
        
    router_logger.info(f"Using fallback model: {fallback}")
    return fallback

def sanitize_for_logging(text: str, max_length: int = 100) -> str:
    """Sanitize text for logging by removing potential secrets and limiting length"""
    if not text:
        return ""
    
    # Common secret patterns to redact
    secret_patterns = [
        (r'(api[_-]?key[\s:=]+)[^\s\'"]+', r'\1[REDACTED]'),
        (r'(bearer[\s]+)[^\s\'"]+', r'\1[REDACTED]'),
        (r'(token[\s:=]+)[^\s\'"]+', r'\1[REDACTED]'),
        (r'(password[\s:=]+)[^\s\'"]+', r'\1[REDACTED]'),
        (r'(secret[\s:=]+)[^\s\'"]+', r'\1[REDACTED]'),
    ]
    
    import re
    sanitized = str(text)
    for pattern, replacement in secret_patterns:
        sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
    
    # Limit length and add ellipsis if truncated
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "..."
        
    return sanitized

# ----- Failure reporting helpers -----
def _compose_failure_report(task, telemetry, local_out, budget_state):
    kind = task.get("kind","*")
    risk = task.get("risk","low")
    prompt = task.get("prompt","")
    tok = _tok_estimate(prompt)
    attempts_lines = []
    for a in telemetry.get("attempts", []):
        # Hide timeout details from user output - these are logged separately
        if a['outcome'] == 'timeout':
            # Only show if it's not a Qwen timeout (since those have automatic fallbacks now)
            if 'qwen' not in a.get('tier', '').lower():
                line = f"- {a['tier']:8s} | network delay | trying alternatives..."
                attempts_lines.append(line)
        else:
            line = f"- {a['tier']:8s} | {a['outcome']:7s} | conf={a.get('confidence','-')} | note={a.get('note','')}"
            attempts_lines.append(line)
    attempts_txt = "\n".join(attempts_lines) if attempts_lines else "(no attempts recorded)"
    budget_msg = "ok"
    if budget_state == "exhausted":
        budget_msg = "exhausted (per-minute cap reached)"
    elif budget_state == "blocked":
        budget_msg = "blocked (circuit breaker)"
    elif budget_state == "skipped":
        budget_msg = "skipped (routine or no need)"
    # options
    options = [
        "retry_local        → try local only again (no cloud)",
        "retry_cloud        → allow cloud escalation once (ignores budget for this task)",
        "force:<model>      → pick a specific free model (qwen3-coder-30b-a3b-instruct-480b-distill-v2:free | glm-4.5-air:free | moonshot/kimi-k2:free | deepseek/deepseek-r1:free)",
        "queue              → defer and auto-retry when cloud budget refills",
        "lower_conf:<0.65>  → accept lower local confidence temporarily",
        "explain            → ask for more detail on any step"
    ]
    options_txt = "\n".join([f"  - {o}" for o in options])
    local_preview = (local_out.get("text","") or "").strip()
    if len(local_preview) > 600:
        local_preview = local_preview[:600] + " …"
    detail = f"""❗ All routes failed to reach the required confidence/budgets for this task.

Task
- kind: {kind}
- risk: {risk}
- tokens_estimate: ~{tok}

Routing Summary
{attempts_txt}

Cloud budget: {budget_msg}
Circuit breakers: {', '.join(k for k,v in _breaker.items() if v>time.time()) or 'none active'}

Local result (kept for now)
---
{local_preview or '(empty)'} 
---

How should I proceed? Choose one:
{options_txt}

(You can also set overrides in the task dict: {{'override':'retry_cloud'|'retry_local'|'queue'|'force:model'|'lower_conf:0.65'}})"""
    return detail

def _telemetry_attempt(tier, outcome, confidence=None, note=None):
    return {"tier": tier, "outcome": outcome, "confidence": confidence, "note": note, "ts": time.time()}


CONF_MIN           = float(os.getenv("AI_CONFIDENCE_MIN", "0.75"))
LOCAL_CONF_MIN     = float(os.getenv("AI_LOCAL_CONF_MIN", "0.68"))
LOCAL_MAX_ATTEMPTS = int(os.getenv("AI_LOCAL_MAX_ATTEMPTS", "2"))
LOCAL_STRICT       = os.getenv("AI_LOCAL_STRICT", "1") == "1"

TTL_CACHE          = int(os.getenv("AI_TTL_CACHE_SEC", "60"))
MAX_HOPS_ROUTINE   = int(os.getenv("AI_MAX_HOPS_ROUTINE", "1"))
MAX_HOPS_CRITICAL  = int(os.getenv("AI_MAX_HOPS_CRITICAL", "3"))
CLOUD_BUDGET_PER_MIN = int(os.getenv("OPENROUTER_BUDGET_PER_MIN", "60"))
CHAT_BUDGET_PER_MIN = int(os.getenv("OPENROUTER_CHAT_BUDGET_PER_MIN", "30"))  # Separate budget for chat
BACKGROUND_BUDGET_PER_MIN = int(os.getenv("OPENROUTER_BACKGROUND_BUDGET_PER_MIN", "30"))  # Separate budget for background tasks

LM_STUDIO_URL      = os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1")
OPENROUTER_URL     = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
# Routing preference: cloud_first or local_first (cloud_first by default)
ROUTING_MODE       = os.getenv("AI_ROUTING_MODE", "cloud_first").strip().lower()

# Dynamic model detection for LM Studio
_lm_studio_model_cache = None
_lm_studio_model_cache_time = 0

# Thread-safe cache and breaker management (must be early for _bucket_allow)
_cache_lock = threading.RLock()
_cache = {}
_breaker = {}
_recent_timeouts = deque(maxlen=50)

# Model rotation for rate limit avoidance
_model_rotation_index = {"qwen": 0, "glm": 0, "kimi": 0, "nemo": 0, "r1": 0}
_model_alternatives = {
    "qwen": [
        "qwen/qwen3-coder:free",
        "qwen/qwen3.5-coder:free", 
        "qwen/qwen2.5-coder-14b-instruct:free",
        "qwen/qwen2-72b-instruct:free"
    ],
    "glm": [
        "z-ai/glm-4.5-air:free",
        "z-ai/glm-4-flash:free",
        "z-ai/glm-4-air:free"
    ],
    "kimi": [
        "moonshot/kimi-k2:free",
        "moonshot/moonshot-v1-8k:free"
    ],
    "nemo": [
        "qwen/qwen3-coder:free",  # Fallback to Qwen for nemo
        "z-ai/glm-4.5-air:free"   # Fallback to GLM
    ],
    "r1": [
        "deepseek/deepseek-r1:free",
        "deepseek/deepseek-v3:free"
    ]
}

def get_next_model_in_rotation(tier_name):
    """Get next model in rotation to avoid rate limits"""
    global _model_rotation_index
    
    if tier_name not in _model_alternatives:
        return None
        
    alternatives = _model_alternatives[tier_name]
    if not alternatives:
        return None
        
    # Get current index and increment for next time
    current_index = _model_rotation_index[tier_name]
    _model_rotation_index[tier_name] = (current_index + 1) % len(alternatives)
    
    selected_model = alternatives[current_index]
    router_logger.info(f"[LOADING] Model rotation: {tier_name} -> {selected_model} (index {current_index})")
    return selected_model

def _apply_paid_variant(model_id: str) -> str:
    try:
        if str(os.getenv("USE_PAID_MODEL_VARIANTS", "0")).strip().lower() in ("1","true","yes"):
            if model_id and model_id.endswith(":free"):
                return model_id.rsplit(":",1)[0]
    except Exception:
        pass
    return model_id

def get_model_for_tier(tier_name, env_var_primary=None, env_var_secondary=None, default_model=None):
    """Get model for tier with smart rotation when rate limited"""
    # First check if we have a manual override via environment variables
    if env_var_primary and os.getenv(env_var_primary):
        return _apply_paid_variant(os.getenv(env_var_primary))
    if env_var_secondary and os.getenv(env_var_secondary):
        return _apply_paid_variant(os.getenv(env_var_secondary))
    
    # If no environment override, use rotation or default
    rotated_model = get_next_model_in_rotation(tier_name)
    if rotated_model:
        return _apply_paid_variant(rotated_model)
        
    return _apply_paid_variant(default_model)

def get_tiers(task=None):
    """Get tiers configuration with intelligent local model selection and rotation"""
    tiers = {
        "local":    {"name":"local",    "base":"lmstudio", "model":get_lm_studio_model(task), "timeout":60},
        "qwen":     {"name":"qwen",     "base":"openrouter","model":get_model_for_tier("qwen", "OR_QWEN_CODER", "AI_MODEL_MAIN_BRAIN", "qwen/qwen3-coder:free"), "timeout":120},
        "glm":      {"name":"glm",      "base":"openrouter","model":get_model_for_tier("glm", "OR_GLM_AIR", None, "z-ai/glm-4.5-air:free"), "timeout":120},
        "nemo":     {"name":"nemo",     "base":"openrouter","model":get_model_for_tier("nemo", "OR_NEMO", None, "qwen/qwen3-coder:free"), "timeout":150},
        "kimi":     {"name":"kimi",     "base":"openrouter","model":get_model_for_tier("kimi", "OR_KIMI", None, "moonshot/kimi-k2:free"), "timeout":120},
        "r1":       {"name":"r1",       "base":"openrouter","model":get_model_for_tier("r1", "OR_R1", None, "deepseek/deepseek-r1:free"), "timeout":180},
    }
    # Optional QwQ reasoning tier
    tiers["qwq"] = {"name":"qwq", "base":"openrouter", "model":get_model_for_tier("qwq", "OR_QWQ", "AI_MODEL_REASONING", "qwen/qwq-32b:free"), "timeout":180}
    return tiers

# Static tier configuration for backwards compatibility
TIERS = get_tiers()

LADDERS = {
    "status":        ["local", "glm"],
    "summary":       ["local", "glm", "kimi"],
    "json_format":   ["local", "qwen", "glm"],
    "code":          ["local", "qwen", "glm"],
    "policy":        ["local", "nemo", "glm"],
    "long_form":     ["local", "qwq", "kimi", "glm", "nemo"],
    "arbiter":       ["local", "qwq", "nemo", "r1"],
    "reasoning":     ["local", "qwq", "r1", "nemo"],
    "*":             ["local", "glm", "qwen"]
}

_bucket_refill_ts = int(time.time() // 60)
_bucket_tokens = CLOUD_BUDGET_PER_MIN

# Separate buckets for chat and background tasks
_chat_bucket_refill_ts = int(time.time() // 60)
_chat_bucket_tokens = CHAT_BUDGET_PER_MIN
_background_bucket_refill_ts = int(time.time() // 60)
_background_bucket_tokens = BACKGROUND_BUDGET_PER_MIN

def _bucket_allow(bucket_type="general"):
    """Allow token consumption from specified bucket type (local mode uses resource-based limits)"""
    global _bucket_tokens, _bucket_refill_ts, _chat_bucket_tokens, _chat_bucket_refill_ts, _background_bucket_tokens, _background_bucket_refill_ts
    
    # In local-only mode, use resource-based rate limiting instead of token-based
    if LOCAL_PARITY_AVAILABLE and os.getenv('AI_LOCAL_ONLY_MODE') == 'true':
        return local_parity.ensure_local_rate_limiting(bucket_type)
    
    with _cache_lock:
        now_min = int(time.time() // 60)
        
        if bucket_type == "chat":
            if now_min != _chat_bucket_refill_ts:
                _chat_bucket_tokens = CHAT_BUDGET_PER_MIN
                _chat_bucket_refill_ts = now_min
            
            if _chat_bucket_tokens > 0:
                _chat_bucket_tokens -= 1
                return True
            else:
                # Log rate limiting action
                if ACTION_LOGGING_AVAILABLE:
                    action_logger.log_rate_limiting_action(
                        bucket_type="chat",
                        action_taken="Request blocked - chat rate limit exceeded",
                        reasoning=f"Chat bucket exhausted: 0/{CHAT_BUDGET_PER_MIN} tokens remaining this minute",
                        bucket_status={"tokens": 0, "limit": CHAT_BUDGET_PER_MIN, "last_refill": _chat_bucket_refill_ts}
                    )
                return False
                
        elif bucket_type == "background":
            if now_min != _background_bucket_refill_ts:
                _background_bucket_tokens = BACKGROUND_BUDGET_PER_MIN
                _background_bucket_refill_ts = now_min
            
            if _background_bucket_tokens > 0:
                _background_bucket_tokens -= 1
                return True
            else:
                # Log rate limiting action
                if ACTION_LOGGING_AVAILABLE:
                    action_logger.log_rate_limiting_action(
                        bucket_type="background",
                        action_taken="Request blocked - background rate limit exceeded",
                        reasoning=f"Background bucket exhausted: 0/{BACKGROUND_BUDGET_PER_MIN} tokens remaining this minute",
                        bucket_status={"tokens": 0, "limit": BACKGROUND_BUDGET_PER_MIN, "last_refill": _background_bucket_refill_ts}
                    )
                return False
        
        else:  # general/legacy bucket
            if now_min != _bucket_refill_ts:
                _bucket_tokens = CLOUD_BUDGET_PER_MIN
                _bucket_refill_ts = now_min
            if _bucket_tokens > 0:
                _bucket_tokens -= 1
                return True
            else:
                # Log rate limiting action
                if ACTION_LOGGING_AVAILABLE:
                    action_logger.log_rate_limiting_action(
                        bucket_type="general",
                        action_taken="Request blocked - general rate limit exceeded",
                        reasoning=f"General bucket exhausted: 0/{CLOUD_BUDGET_PER_MIN} tokens remaining this minute",
                        bucket_status={"tokens": 0, "limit": CLOUD_BUDGET_PER_MIN, "last_refill": _bucket_refill_ts}
                    )
                return False

def _tok_estimate(text:str)->int:
    return max(1, len(text)//3)

def _initial_confidence(task)->float:
    kind = task.get("kind","*")
    base = 0.88 if kind in ("status","summary","json_format","code") else 0.72
    if _tok_estimate(task.get("prompt","")) > 8000: base -= 0.15
    return max(0.0, min(1.0, base))

def _max_hops(task)->int:
    return MAX_HOPS_CRITICAL if task.get("risk","low") in ("medium","high") else MAX_HOPS_ROUTINE

def _ladder(task):
    names = LADDERS.get(task.get("kind","*"), LADDERS["*"])
    # Filter out qwq if not enabled
    try:
        enabled = str(os.getenv("ENABLE_QWQ_REASONING", "0")).strip().lower() in ("1","true","yes")
        if not enabled:
            names = [n for n in names if n != "qwq"]
    except Exception:
        names = [n for n in names if n != "qwq"]
    return names

def _cache_key(task, prompt):
    sig = hashlib.sha256((task.get("kind","*")+"|"+task.get("risk","low")+"|"+prompt).encode()).hexdigest()
    return sig

def _get_cache(key):
    with _cache_lock:
        hit = _cache.get(key)
        if not hit: return None
        exp, val = hit
        if exp > time.time(): return val
        _cache.pop(key, None); return None

def _set_cache(key, val, ttl=TTL_CACHE):
    with _cache_lock:
        _cache[key] = (time.time()+ttl, val)

def _blocked(tier_name):
    with _cache_lock:
        return _breaker.get(tier_name, 0) > time.time()

def _trip(tier_name, cool=600):
    with _cache_lock:
        _breaker[tier_name] = time.time() + cool

def _repair_prompt(kind, original):
    if kind in ("json_format","code"):
        return f"Repair and output strictly valid JSON or code only, no prose. If JSON, ensure compliant: {original}"
    if kind in ("summary","status"):
        return f"Rewrite concisely in 4-6 bullet points with clear labels. Original:\n{original}"
    if kind in ("policy","arbiter"):
        return f"Rewrite with cautious, compliance-safe language and numbered steps. Original:\n{original}"
    return f"Rewrite clearly and concisely. Original:\n{original}"

def call_local(model, prompt, timeout):
    payload = {"model": model, "messages": [
        {"role":"system","content":"You are a concise, accurate assistant. Prefer structured, compact outputs."},
        {"role":"user","content": prompt}
    ], "temperature":0.2, "max_tokens":1024}
    
    # First check if LM Studio is reachable
    try:
        health_check = requests.get(f"{LM_STUDIO_URL}/models", timeout=3)
        if health_check.status_code != 200:
            router_logger.warning(f"LM Studio health check failed: {health_check.status_code}")
            raise TimeoutError("lmstudio not responding")
    except requests.exceptions.Timeout:
        router_logger.warning("LM Studio health check timeout")
        raise TimeoutError("lmstudio health timeout")
    except requests.exceptions.ConnectionError:
        router_logger.warning("LM Studio connection refused")
        raise TimeoutError("lmstudio connection refused")
    
    try:
        r = requests.post(f"{LM_STUDIO_URL}/chat/completions", json=payload, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        text = data["choices"][0]["message"]["content"]
        router_logger.debug(f"[OK] LM Studio response: {len(text)} chars")
        return {"text": text, "confidence": 0.8 if text and len(text)>10 else 0.6}
    except requests.exceptions.Timeout:
        router_logger.warning("⏱️ LM Studio request timeout")
        raise TimeoutError("lmstudio timeout")
    except requests.exceptions.ConnectionError:
        router_logger.warning("[ERROR] LM Studio connection error")
        raise TimeoutError("lmstudio connection error")
    except Exception as e:
        router_logger.error(f"[ERROR] LM Studio error: {e}")
        return {"text": f"(local error) {e}", "confidence": 0.0}

def call_openrouter(model, prompt, timeout):
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json", "X-Title":"DuckBot-AI-Manager"}
    payload = {"model": model, "messages": [
        {"role":"system","content":"You are a concise, accurate assistant. Prefer structured, compact outputs."},
        {"role":"user","content": prompt}
    ], "temperature":0.2, "max_tokens":1536}
    try:
        r = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=timeout)
        
        # Handle rate limiting and other HTTP errors more gracefully
        if r.status_code == 429:
            return {"text": f"[WARNING] {model} is temporarily rate-limited. Try again later or use a different model.", "confidence": 0.0, "rate_limited": True}
        elif r.status_code == 402:
            return {"text": f"[EMOJI] {model} requires payment. Using free models only.", "confidence": 0.0, "payment_required": True}
        elif r.status_code != 200:
            error_data = r.json() if r.headers.get('content-type', '').startswith('application/json') else {"error": r.text}
            return {"text": f"[EMOJI] API Error ({r.status_code}): {error_data.get('error', {}).get('message', 'Unknown error')}", "confidence": 0.0}
            
        data = r.json()
        text = data["choices"][0]["message"]["content"]
        conf = 0.85 if text and len(text) > 12 else 0.5
        return {"text": text, "confidence": conf}
    except requests.exceptions.Timeout:
        raise TimeoutError("openrouter timeout")
    except Exception as e:
        return {"text": f"(or error {model}) {e}", "confidence": 0.0}

def _call_tier(tier_name, prompt, task=None):
    # Use dynamic tier detection with task-aware model selection
    tiers = get_tiers(task)
    tier = tiers[tier_name]
    if tier["base"] == "lmstudio":
        return call_local(tier["model"], prompt, tier["timeout"])
    else:
        return call_openrouter(tier["model"], prompt, tier["timeout"])

def _local_first_sequence(task, prompt):
    attempt = 0
    original_text = None
    last_conf = 0.0
    while attempt < LOCAL_MAX_ATTEMPTS:
        out = _call_tier("local", prompt if attempt==0 else _repair_prompt(task.get("kind","*"), original_text or ""), task)
        original_text = out.get("text", "")
        last_conf = float(out.get("confidence", 0.0))
        if last_conf >= LOCAL_CONF_MIN:
            out["model_used"] = "local"
            return out, True
        attempt += 1
    return {"text": original_text or "(no output)", "confidence": last_conf, "model_used":"local"}, False

def _cloud_escalate_allowed(task):
    long_ctx = _tok_estimate(task.get("prompt","")) > 8000
    risky = task.get("risk","low") in ("medium","high")
    kind = task.get("kind","*")
    needs_cloud_kind = kind in ("policy","arbiter","reasoning","long_form","code","json_format")
    return long_ctx or risky or needs_cloud_kind



def clear_lm_studio_cache():
    """Clear LM Studio model cache to force refresh"""
    global _lm_studio_model_cache, _lm_studio_model_cache_time
    with _cache_lock:
        _lm_studio_model_cache = None
        _lm_studio_model_cache_time = 0
    router_logger.info("LM Studio model cache cleared - will refresh on next detection")

def check_lm_studio_status():
    """Check LM Studio server status and available models"""
    try:
        response = requests.get(f"{LM_STUDIO_URL}/models", timeout=3)
        if response.status_code == 200:
            models = response.json()
            if models.get("data"):
                return {
                    "status": "running", 
                    "models_loaded": len(models["data"]),
                    "model_names": [m["id"] for m in models["data"]]
                }
            else:
                return {"status": "running", "models_loaded": 0, "model_names": []}
        else:
            return {"status": "error", "code": response.status_code}
    except requests.exceptions.ConnectionError:
        return {"status": "not_running"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def get_router_state():
    """Return internal router state for WebUI."""
    with _cache_lock:
        # Check if we're using OpenRouter models primarily
        openrouter_models = [
            os.getenv("AI_MODEL_MAIN_BRAIN"),
            os.getenv("AI_MODEL_CODE"),
            os.getenv("AI_MODEL_DEBUG"),
            os.getenv("AI_MODEL_ANALYSIS")
        ]
        active_openrouter = [m for m in openrouter_models if m and ("qwen/" in m or "glm/" in m)]
        
        if active_openrouter:
            # Using OpenRouter - show primary brain model
            current_model = os.getenv("AI_MODEL_MAIN_BRAIN", "qwen/qwen3-coder:free")
        else:
            # Check LM Studio
            current_model = get_lm_studio_model()
            
        # Get available models and LM Studio status
        available_models = get_available_local_models()
        lm_studio_status = check_lm_studio_status()
        
        return {
            "bucket_tokens": _bucket_tokens,
            "bucket_limit": CLOUD_BUDGET_PER_MIN,
            "bucket_refill_min_epoch": _bucket_refill_ts,
            "chat_bucket_tokens": _chat_bucket_tokens,
            "chat_bucket_limit": CHAT_BUDGET_PER_MIN,
            "background_bucket_tokens": _background_bucket_tokens,
            "background_bucket_limit": BACKGROUND_BUDGET_PER_MIN,
            "breakers": {k:int(v) for k,v in _breaker.items()},
            "cache_size": len(_cache),
            "current_lm_model": current_model,
            "lm_studio_url": LM_STUDIO_URL,
            "lm_studio_status": lm_studio_status,
            "available_local_models": available_models,
            "preferred_model": os.getenv("LM_STUDIO_MODEL", available_models[0]["id"]) if available_models else "nvidia_NVIDIA-Nemotron-Nano-9B-v2-GGUF/nvidia_NVIDIA-Nemotron-Nano-9B-v2-Q5_K_S.gguf",
            "routing_mode": ROUTING_MODE,
            "current_cloud_model": os.getenv("AI_MODEL_MAIN_BRAIN", "qwen/qwen3-coder:free"),
            "config": {
                "CONF_MIN": CONF_MIN,
                "LOCAL_CONF_MIN": LOCAL_CONF_MIN,
                "LOCAL_MAX_ATTEMPTS": LOCAL_MAX_ATTEMPTS,
                "TTL_CACHE": TTL_CACHE,
                "MAX_HOPS_ROUTINE": MAX_HOPS_ROUTINE,
                "MAX_HOPS_CRITICAL": MAX_HOPS_CRITICAL,
            }
        }

def clear_cache():
    with _cache_lock:
        _cache.clear()
    return True

def reset_breakers():
    with _cache_lock:
        _breaker.clear()
    return True

def get_available_local_models():
    """Get list of actually available local models from LM Studio"""
    try:
        r = requests.get(f"{LM_STUDIO_URL}/models", timeout=3)
        data = r.json() if r.status_code == 200 else {}
        items = []
        for m in (data.get("data") or []):
            mid = (m.get("id") or m.get("model") or "").strip()
            if not mid:
                continue
            name = m.get("name") or mid
            items.append({"id": mid, "name": name, "description": m.get("description", ""), "size": m.get("size", ""), "specialty": m.get("tags", "")})
        return items
    except Exception:
        # Fallback minimal list when LM Studio not reachable
        return [
            {"id": "qwen/qwen3-coder-30b", "name": "Qwen3 Coder 30B", "description": "Coding-focused", "size": "30B", "specialty": "coding"},
            {"id": "qwen/qwen3-30b-a3b", "name": "Qwen3 30B", "description": "General purpose", "size": "30B", "specialty": "general"},
        ]

def select_optimal_local_model(task, available):
    """Pick best local model from LM Studio list based on task type."""
    kind = (task or {}).get("kind", "*")
    ids = [m.get("id","") for m in (available or [])]
    preferred = []
    if kind in ("code", "json_format", "debugging", "analysis"):
        preferred = ["coder", "code"]
    else:
        preferred = ["qwen3", "qwen"]
    for p in preferred:
        for mid in ids:
            if p in mid.lower():
                return mid
    return os.getenv("LM_STUDIO_MODEL") or (ids[0] if ids else "No model loaded")

def get_lm_studio_model_smart(task=None):
    avail = get_available_local_models()
    return select_optimal_local_model(task or {}, avail)

def set_local_model_preference(model_id):
    """Set preferred local model via environment variable"""
    os.environ["LM_STUDIO_MODEL"] = model_id
    # Clear cache to force refresh
    refresh_lm_studio_model()
    return model_id

def enhance_with_qwen_tools(task, response):
    """Enhance response with Qwen Code tools if beneficial and available"""
    if not can_use_qwen_code_tools(task):
        return response
        
    try:
        from duckbot.qwen_diagnostics import QwenDiagnostics
        qwen = QwenDiagnostics()
        
        if not qwen.qwen_available:
            return response
            
        # For code tasks, add Qwen Code analysis if helpful
        kind = task.get("kind", "*")
        prompt = task.get("prompt", "")
        
        if kind in ("code", "debugging", "analysis") and len(prompt) > 20:
            try:
                # Get enhanced analysis from Qwen Code tools
                analysis = qwen.analyze_code_prompt(prompt)
                if analysis:
                    original_text = response.get("text", "")
                    enhanced_text = f"{original_text}\n\n### Qwen Code Analysis\n{analysis}"
                    response["text"] = enhanced_text
                    response["enhanced_with_qwen"] = True
                    router_logger.info("Enhanced response with Qwen Code tools")
            except Exception as e:
                router_logger.warning(f"Qwen Code enhancement failed: {e}")
                
        # Optionally augment with Qwen-Agent for planning/tool-use across all base models
        try:
            if ENHANCED_AI_AVAILABLE and len(prompt) > 12 and kind in ("status","summary","reasoning","long_form","arbiter","code","analysis","json_format"):
                import asyncio
                agent_result = None
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # Avoid nested event loop in async contexts; skip agent enhancement here
                        agent_result = None
                    else:
                        from duckbot.qwen_agent_integration import execute_enhanced_task
                        agent_result = asyncio.run(execute_enhanced_task(prompt, {"task": task}))
                except RuntimeError:
                    # No running loop; safe to create one
                    try:
                        from duckbot.qwen_agent_integration import execute_enhanced_task
                        agent_result = asyncio.run(execute_enhanced_task(prompt, {"task": task}))
                    except Exception:
                        agent_result = None
                except Exception:
                    agent_result = None
                if agent_result and agent_result.get("success") and agent_result.get("response"):
                    original_text = response.get("text", "")
                    agent_text = str(agent_result.get("response"))
                    response["text"] = f"{original_text}\n\n### Qwen-Agent Augmentation\n{agent_text}"
                    response["enhanced_with_qwen_agent"] = True
        except Exception as e:
            router_logger.warning(f"Qwen-Agent enhancement skipped: {e}")

    except ImportError:
        pass  # Qwen diagnostics not available
    except Exception as e:
        router_logger.warning(f"Could not enhance with Qwen tools: {e}")
        
    return response


async def enhanced_chat_completion(messages, task_type="general", user_id=None, context=None, stream=False):
    """Enhanced chat completion using intelligent agents and provider connectors"""
    
    # Create context for intelligent agents
    agent_context = None
    if CONTEXT_MANAGEMENT_AVAILABLE:
        try:
            context_data = {
                "messages": messages,
                "task_type": task_type,
                "user_id": user_id,
                "timestamp": time.time()
            }
            agent_context = AgentContext(
                user_id=user_id,
                timestamp=time.time(),
                environment=context_data,
                metadata={"task_type": task_type}
            )
            
            # Store context for learning
            await create_context(context_data, {"source": "ai_router"}, [task_type])
        except Exception as e:
            router_logger.error(f"Error creating context: {e}")
    
    # Use intelligent agents for decision making
    if INTELLIGENT_AGENTS_AVAILABLE and agent_context:
        try:
            decision = await analyze_with_intelligence(task_type, {
                "messages": messages,
                "context": context
            }, agent_context)
            
            if decision.confidence > 0.7:
                # High confidence - use agent recommendation
                if decision.action == "use_specific_provider":
                    recommended_provider = decision.data.get("provider")
                    if recommended_provider and ENHANCED_CONNECTORS_AVAILABLE:
                        if stream:
                            yield {"type": "thought", "data": f"Agent decided to use {recommended_provider}"}
                            async for chunk in stream_chat(messages, provider=recommended_provider):
                                yield {"type": "content", "data": chunk}
                            return
                        else:
                            result = await complete_chat(messages, provider=recommended_provider)
                            if result.get("success"):
                                return result
                        
                elif decision.action == "enhanced_response":
                    # Agent provided enhanced response
                    if stream:
                        yield {"type": "thought", "data": "Agent generated an enhanced response"}
                        yield {"type": "content", "data": decision.data.get("response", "")}
                        return
                    else:
                        return {
                            "success": True,
                            "content": decision.data.get("response", ""),
                            "model": decision.agent_type,
                            "confidence": decision.confidence,
                            "reasoning": decision.reasoning,
                            "enhanced_by_agent": True
                        }
        except Exception as e:
            router_logger.error(f"Error using intelligent agents: {e}")
    
    # Fall back to enhanced connectors
    if ENHANCED_CONNECTORS_AVAILABLE:
        try:
            if stream:
                yield {"type": "thought", "data": "Using default provider"}
                async for chunk in stream_chat(messages):
                    yield {"type": "content", "data": chunk}
                return
            else:
                result = await complete_chat(messages)
                
                # Learn from the result
                if CONTEXT_MANAGEMENT_AVAILABLE and agent_context:
                    try:
                        success = result.get("success", False)
                        await learn_from_experience(
                            context_data={
                                "messages": messages,
                                "task_type": task_type
                            },
                            outcome=result,
                            success=success,
                            context_type=task_type
                        )
                    except Exception as e:
                        router_logger.error(f"Error learning from experience: {e}")
                
                return result
        except Exception as e:
            router_logger.error(f"Error using enhanced connectors: {e}")
    
    # Legacy fallback
    if stream:
        yield {"type": "error", "data": "No streaming provider available"}
    else:
        return None

def enhance_with_claude_code_tools(task, response):
    """Enhance response with Claude Code tools if beneficial and available"""
    if not can_use_claude_code_tools(task):
        return response
        
    try:
        if not CLAUDE_CODE_AVAILABLE:
            return response
            
        # For code tasks, add Claude Code analysis if helpful
        kind = task.get("kind", "*")
        prompt = task.get("prompt", "")
        
        if kind in ("code", "debugging", "analysis", "review") and len(prompt) > 20:
            try:
                # Get enhanced analysis from Claude Code tools
                import asyncio
                
                # Create context for Claude Code
                context = {
                    "task_kind": kind,
                    "original_prompt": prompt,
                    "original_response": response.get("text", ""),
                    "model_used": response.get("model_used", "unknown")
                }
                
                # Check if we can run async code
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # Skip Claude Code enhancement in async context to avoid nested loops
                        router_logger.debug("Skipping Claude Code enhancement in async context")
                        return response
                    else:
                        claude_result = asyncio.run(execute_claude_code_task(prompt, context))
                except:
                    # Fallback - try without async
                    try:
                        claude_result = asyncio.run(execute_claude_code_task(prompt, context))
                    except:
                        return response
                
                if claude_result and claude_result.get("success"):
                    original_text = response.get("text", "")
                    claude_analysis = claude_result.get("response", "")
                    if claude_analysis and len(claude_analysis) > 10:
                        enhanced_text = f"{original_text}\n\n### Claude Code Analysis\n{claude_analysis}"
                        response["text"] = enhanced_text
                        response["enhanced_with_claude"] = True
                        response["claude_model"] = claude_result.get("model", "unknown")
                        router_logger.info("Enhanced response with Claude Code tools")
                        
            except Exception as e:
                router_logger.warning(f"Claude Code enhancement failed: {e}")
                
    except ImportError:
        pass  # Claude Code integration not available
    except Exception as e:
        router_logger.warning(f"Could not enhance with Claude Code tools: {e}")
        
    return response


def refresh_lm_studio_model():
    """Force refresh of LM Studio model detection"""
    global _lm_studio_model_cache, _lm_studio_model_cache_time
    with _cache_lock:
        _lm_studio_model_cache = None
        _lm_studio_model_cache_time = 0
        # Trigger fresh detection
        new_model = get_lm_studio_model()
        return new_model


def _handle_qwen_timeout_fallback(prompt, task, telemetry):
    """
    Handle Qwen timeout with automatic fallback: Qwen → GLM 4.5 Air → Local
    Returns successful result or None if all fallbacks fail
    """
    router_logger.info("[FALLBACK] Qwen timeout detected - attempting GLM 4.5 Air fallback")
    user_id = task.get("user_id")
    
    # Log the initial fallback decision
    if ACTION_LOGGING_AVAILABLE:
        action_logger.log_fallback_decision(
            original_model="qwen",
            fallback_model="glm-4.5-air",
            error_type="timeout",
            reasoning="Qwen model timed out, automatically falling back to GLM 4.5 Air for reliability",
            attempt_number=1,
            user_id=user_id
        )
    
    # Try GLM 4.5 Air first
    try:
        glm_result = _call_tier("glm", prompt, task)
        if glm_result and glm_result.get("confidence", 0.0) >= CONF_MIN:
            glm_result["model_used"] = "glm"
            router_logger.info("[FALLBACK] GLM 4.5 Air fallback successful")
            telemetry["attempts"].append(_telemetry_attempt("glm", "ok", glm_result.get("confidence"), note="qwen_timeout_fallback"))
            glm_result['telemetry'] = telemetry
            return glm_result
        else:
            telemetry["attempts"].append(_telemetry_attempt("glm", "lowconf", glm_result.get("confidence", 0.0), note="qwen_timeout_fallback")
    except TimeoutError:
        router_logger.warning("[FALLBACK] GLM 4.5 Air also timed out - trying local fallback")
        telemetry["attempts"].append(_telemetry_attempt("glm", "timeout", None, note="qwen_timeout_fallback")
        
        # Log the second fallback decision
        if ACTION_LOGGING_AVAILABLE:
            action_logger.log_fallback_decision(
                original_model="glm-4.5-air",
                fallback_model="local",
                error_type="timeout",
                reasoning="GLM 4.5 Air also timed out, falling back to local LM Studio model as final fallback",
                attempt_number=2,
                user_id=user_id
            )
    except Exception as e:
        router_logger.error(f"[ERROR] GLM 4.5 Air fallback failed: {e}")
        telemetry["attempts"].append(_telemetry_attempt("glm", "error", None, note=f"qwen_timeout_fallback_error: {str(e)}"))
    
    # Try Local as final fallback
    router_logger.info("[LOADING] Attempting local fallback after Qwen timeout")
    try:
        local_result = _call_tier("local", prompt, task)
        if local_result:
            local_result["model_used"] = "local"
            router_logger.info("[OK] Local fallback successful after Qwen timeout")
            telemetry["attempts"].append(_telemetry_attempt("local", "ok", local_result.get("confidence", 0.0), note="qwen_timeout_final_fallback"))
            local_result['telemetry'] = telemetry
            return local_result
    except Exception as e:
        router_logger.error(f"[ERROR] Local fallback also failed: {e}")
        telemetry["attempts"].append(_telemetry_attempt("local", "error", None, note=f"qwen_timeout_final_fallback_error: {str(e)}"))
    
    # All fallbacks failed
    router_logger.error("[ERROR] All Qwen timeout fallbacks failed")
    return None

def _route_task_impl(task, bucket_type="general"):
    """Internal implementation of route_task - wrapped for exception handling"""
    with _agent_lock:
        if AGENT_PAUSED:
            return {"text": "Agent is paused. Please resume to continue.", "confidence": 1.0, "model_used": "system"}

    prompt = (task.get("prompt","") or "").strip()
    
    # Check for server management tasks first (high priority)
    server_result = handle_server_management_task(task)
    if server_result:
        return server_result
    
    key = _cache_key(task, prompt)
    cached = _get_cache(key)
    if cached:
        out = dict(cached); out["cached"] = True; return out

    override = (task.get("override") or "").strip().lower()
    force_model = None
    lower_conf = None
    if override.startswith("force:"):
        force_model = override.split("force:",1)[1].strip()
    if override.startswith("lower_conf:"):
        try:
            lower_conf = float(override.split("lower_conf:",1)[1].strip())
        except Exception:
            lower_conf = None

    telemetry = {"attempts": []}
    budget_state = "ok"

    # Cloud-first fast path when configured (unless explicitly forcing local)
    try_cloud_first = (ROUTING_MODE == "cloud_first" and override != "retry_local" and not force_model)
    if try_cloud_first:
        # Respect budget unless explicitly retrying cloud
        if not _bucket_allow(bucket_type) and override != "retry_cloud":
            budget_state = "exhausted"
        else:
            # Prioritize Qwen as main brain, then other cloud tiers in ladder order
            cloud_tiers = ["qwen"] + [t for t in _ladder(task) if t not in ("local", "qwen")]
            hops = 0
            for tier_name in cloud_tiers:
                if hops >= (MAX_HOPS_CRITICAL if task.get("risk","low") in ("medium","high") else MAX_HOPS_ROUTINE) and override not in ("retry_cloud",):
                    break
                if _blocked(tier_name):
                    telemetry["attempts"].append(_telemetry_attempt(tier_name, "blocked", None, note="circuit breaker")
                    continue
                try:
                    out = _call_tier(tier_name, prompt, task)
                    out["model_used"] = tier_name
                    telemetry["attempts"].append(_telemetry_attempt(tier_name, "ok", out.get("confidence")))
                    if out.get("confidence",0.0) >= CONF_MIN:
                        _set_cache(key, out)
                        out['telemetry']=telemetry
                        out['budget_state']=budget_state
                        return out
                except TimeoutError:
                    router_logger.warning(f"⏱️ {tier_name} timeout - attempting automatic fallback")
                    telemetry["attempts"].append(_telemetry_attempt(tier_name, "timeout", None))
                    _trip(tier_name, cool=600)
                    
                    # Implement specific Qwen → GLM → Local fallback for timeouts
                    if tier_name == "qwen":
                        timeout_fallback_result = _handle_qwen_timeout_fallback(prompt, task, telemetry)
                        if timeout_fallback_result:
                            return timeout_fallback_result
                hops += 1

    # 1) Local attempts (with optional lower_conf override) then optional cloud
    orig_local_conf = LOCAL_CONF_MIN
    local_conf_min = lower_conf if (lower_conf and lower_conf < LOCAL_CONF_MIN) else LOCAL_CONF_MIN

    # try local up to LOCAL_MAX_ATTEMPTS; second pass is repair
    attempt = 0
    original_text = None
    last_conf = 0.0
    while attempt < LOCAL_MAX_ATTEMPTS:
        out = _call_tier("local", prompt if attempt==0 else _repair_prompt(task.get("kind","*"), original_text or ""), task)
        original_text = out.get("text", "")
        last_conf = float(out.get("confidence", 0.0))
        telemetry["attempts"].append(_telemetry_attempt("local", "ok", last_conf, note="pass"+str(attempt+1)))
        if last_conf >= local_conf_min:
            out["model_used"] = "local"
            _set_cache(key, out)
            return out
        attempt += 1

    local_out = {"text": original_text or "(no output)", "confidence": last_conf, "model_used":"local"}

    # 2) Decide if cloud escalation is allowed
    def _needs_cloud(task):
        long_ctx = _tok_estimate(task.get("prompt","")) > 8000
        risky = task.get("risk","low") in ("medium","high")
        kind = task.get("kind","*")
        needs_cloud_kind = kind in ("policy","arbiter","reasoning","long_form","code","json_format")
        return long_ctx or risky or needs_cloud_kind

    allow_cloud = _needs_cloud(task) or override in ("retry_cloud",) or force_model

    # routine and not needed -> keep local
    if task.get("risk","low") == "low" and not allow_cloud and override != "retry_cloud":
        fail_text = _compose_failure_report(task, telemetry, local_out, budget_state="skipped")
        return {"text": fail_text, "confidence": local_out.get("confidence",0.0), "model_used":"local", "failure": True}

    # budget check
    if not _bucket_allow(bucket_type) and not (override in ("retry_cloud",) or force_model):
        budget_state = "exhausted"
        fail_text = _compose_failure_report(task, telemetry, local_out, budget_state)
        return {"text": fail_text, "confidence": local_out.get("confidence",0.0), "model_used":"local", "failure": True, "note":"cloud_budget_exhausted"}

    # 3) Cloud escalation
    hops = 0
    # force a specific model if requested
    if force_model:
        try:
            out = call_openrouter(force_model, prompt, timeout=14)
            telemetry["attempts"].append(_telemetry_attempt("force", "ok", out.get("confidence"), note=force_model))
            if out.get("confidence",0.0) >= CONF_MIN:
                out["model_used"] = force_model
                _set_cache(key, out)
                out['telemetry']=telemetry
                out['budget_state']=budget_state if 'budget_state' in locals() else 'ok'
                return out
            else:
                telemetry["attempts"].append(_telemetry_attempt("force", "lowconf", out.get("confidence"), note="below threshold")
        except TimeoutError:
            router_logger.warning(f"⏱️ Forced model {force_model} timeout")
            telemetry["attempts"].append(_telemetry_attempt("force", "timeout", None, note=force_model))
            
            # If forcing a Qwen model that times out, try the same fallback
            if "qwen" in force_model.lower():
                timeout_fallback_result = _handle_qwen_timeout_fallback(prompt, task, telemetry)
                if timeout_fallback_result:
                    return timeout_fallback_result

    for tier_name in _ladder(task):
        if tier_name == "local":
            continue
        if hops >= (MAX_HOPS_CRITICAL if task.get("risk","low") in ("medium","high") else MAX_HOPS_ROUTINE) and override not in ("retry_cloud",):
            break
        if _blocked(tier_name):
            telemetry["attempts"].append(_telemetry_attempt(tier_name, "blocked", None, note="circuit breaker")
            continue
        try:
            out = _call_tier(tier_name, prompt)
            out["model_used"] = tier_name
            telemetry["attempts"].append(_telemetry_attempt(tier_name, "ok", out.get("confidence")))
            if out.get("confidence",0.0) >= CONF_MIN:
                _set_cache(key, out)
                out['telemetry']=telemetry
                out['budget_state']=budget_state if 'budget_state' in locals() else 'ok'
                return out
        except TimeoutError:
            router_logger.warning(f"⏱️ {tier_name} timeout - attempting automatic fallback")
            telemetry["attempts"].append(_telemetry_attempt(tier_name, "timeout", None))
            _trip(tier_name, cool=600)
            
            # Implement specific Qwen → GLM → Local fallback for timeouts
            if tier_name == "qwen":
                timeout_fallback_result = _handle_qwen_timeout_fallback(prompt, task, telemetry)
                if timeout_fallback_result:
                    return timeout_fallback_result
        hops += 1

    # 4) Failure path → detailed report + options
    fail_text = _compose_failure_report(task, telemetry, local_out, budget_state)
    return {"text": fail_text, "confidence": local_out.get("confidence",0.0), "model_used":"local", "failure": True}

    # 1) Local-first attempts
    local_out, local_ok = _local_first_sequence(task, prompt)
    if LOCAL_STRICT and local_ok:
        _set_cache(key, local_out)
        return local_out

    # If routine and no specific need to escalate, keep local
    if task.get("risk","low") == "low" and not _cloud_escalate_allowed(task):
        _set_cache(key, local_out)
        return local_out

    # 2) Cloud escalation only if bucket allows
    if not _bucket_allow(bucket_type):
        local_out["note"] = "cloud_budget_exhausted"
        _set_cache(key, local_out)
        return local_out

    hops = 0
    for tier_name in _ladder(task):
        if tier_name == "local":
            continue
        if hops >= (MAX_HOPS_CRITICAL if task.get("risk","low") in ("medium","high") else MAX_HOPS_ROUTINE):
            break
        if _blocked(tier_name):
            continue
        try:
            out = _call_tier(tier_name, prompt)
            out["model_used"] = tier_name
            if out.get("confidence",0.0) >= CONF_MIN:
                _set_cache(key, out)
                out['telemetry']=telemetry
                out['budget_state']=budget_state if 'budget_state' in locals() else 'ok'
                return out
        except TimeoutError:
            router_logger.warning(f"⏱️ {tier_name} timeout - attempting automatic fallback")
            _trip(tier_name, cool=600)
            
            # Implement specific Qwen → GLM → Local fallback for timeouts
            if tier_name == "qwen":
                timeout_fallback_result = _handle_qwen_timeout_fallback(prompt, task, telemetry if 'telemetry' in locals() else {"attempts": []})
                if timeout_fallback_result:
                    return timeout_fallback_result
        hops += 1

    _set_cache(key, local_out)
    return local_out

def route_task(task, bucket_type="general"):
    """
    Main router entry point with comprehensive exception handling
    task = {"kind": "...", "risk": "low|medium|high", "prompt": "...", "override": "retry_cloud|retry_local|force:model|queue|lower_conf:0.65"}
    bucket_type = "chat"|"background"|"general" - determines which rate limit bucket to use
    """
    global _bucket_tokens, _chat_bucket_tokens, _background_bucket_tokens
    start_time = time.time()
    prompt = task.get("prompt", "")
    user_id = task.get("user_id")
    
    try:
        # Ensure system is initialized before processing tasks (except system_init)
        if task.get("kind") != "system_init":
            ensure_system_initialized()
            
        # Lazy auto-ingest if index empty
        try:
            stats = index_stats()
            if stats.get("chunks", 0) == 0:
                try:
                    auto_ingest_defaults()
                except Exception:
                    pass
        except Exception:
            pass

        # RAG: maybe augment prompt
        augmented_task, rag_info = maybe_augment_with_rag(task)

        response = _route_task_impl(augmented_task, bucket_type)
        # Enhance with Qwen Code tools if beneficial
        enhanced_response = enhance_with_qwen_tools(task, response)
        
        # Further enhance with Claude Code tools if beneficial
        enhanced_response = enhance_with_claude_code_tools(task, enhanced_response)
        
        # Log successful routing decision
        if ACTION_LOGGING_AVAILABLE:
            execution_time = int((time.time() - start_time) * 1000)
            chosen_model = enhanced_response.get("model_used", "unknown")
            confidence = enhanced_response.get("confidence", 0.0)
            
            # Determine reasoning based on routing outcome
            if enhanced_response.get("cached"):
                reasoning = f"Served from cache for efficiency. Model: {chosen_model}, Confidence: {confidence:.2f}"
            elif enhanced_response.get("failure"):
                reasoning = f"All models failed or rate limited. Bucket: {bucket_type}"
            else:
                telemetry = enhanced_response.get("telemetry", {})
                attempts = telemetry.get("attempts", [])
                reasoning = f"Selected {chosen_model} after {len(attempts)} attempts. Bucket: {bucket_type}, Confidence: {confidence:.2f}"
                if len(attempts) > 1:
                    reasoning += f" (Failed models: {[a['tier'] for a in attempts[:-1] if a['outcome'] != 'ok']})"
            
            # Get rate limit status for context
            rate_limit_status = {
                "chat_tokens": _chat_bucket_tokens,
                "background_tokens": _background_bucket_tokens,
                "general_tokens": _bucket_tokens
            }
            
            action_logger.log_ai_routing_decision(
                prompt=prompt,
                chosen_model=chosen_model,
                reasoning=reasoning,
                available_models=_get_available_models(),
                rate_limit_status=rate_limit_status,
                execution_time_ms=execution_time,
                outcome=f"Success: {confidence:.2f}" if not enhanced_response.get("failure") else "Failed",
                user_id=user_id,
                bucket_type=bucket_type
            )
        
        # Attach RAG info to response for observability
        if isinstance(enhanced_response, dict):
            enhanced_response.setdefault("rag_used", rag_info.get("used", False))
            if rag_info.get("used"):
                enhanced_response.setdefault("rag_chunks", rag_info.get("chunks", []))
        
        # Apply local feature parity enhancements if in local-only mode
        if LOCAL_PARITY_AVAILABLE and os.getenv('AI_LOCAL_ONLY_MODE') == 'true':
            enhanced_response = ensure_full_local_parity(task, enhanced_response)
            
        return enhanced_response
    except Exception as e:
        # Log the routing error
        if ACTION_LOGGING_AVAILABLE:
            execution_time = int((time.time() - start_time) * 1000)
            action_logger.log_action(
                action_type="AI_ROUTING",
                component="ai_router_gpt",
                action_description=f"Router exception: {type(e).__name__}",
                reasoning=f"Unexpected error during routing: {sanitize_for_logging(str(e))}",
                context_data={"task_kind": task.get("kind"), "bucket_type": bucket_type},
                outcome="Error",
                execution_time_ms=execution_time,
                user_id=user_id,
                severity="ERROR"
            )
        
        # Sanitize error message for logging
        safe_error = sanitize_for_logging(str(e))
        router_logger.error(f"Router exception: {safe_error}")
        
        # Create safe fallback response with sanitized error
        fallback = {
            "text": f"Router error: {sanitize_for_logging(str(e), 200)}... Please check logs and try again.",
            "confidence": 0.1,
            "model_used": "error_handler",
            "failure": True,
            "error_type": type(e).__name__,
            "telemetry": {"attempts": [{"tier": "error", "outcome": "exception", "note": sanitize_for_logging(str(e), 100)}]}
        }
        
        # Try to log to file as well (sanitized)
        try:
            from pathlib import Path
            error_log = Path(__file__).parent / "router_errors.log"
            with open(error_log, "a", encoding="utf-8") as f:
                # Sanitize the full traceback
                safe_traceback = sanitize_for_logging(traceback.format_exc(), 1000)
                f.write(f"{time.time()}: Router exception: {safe_error}\n{safe_traceback}\n---\n")
        except Exception:
            pass  # Don't crash on logging failure
            
        return fallback

# -----------------
# Local model helpers (filesystem fallback if LM Studio API unavailable)
# -----------------
def _candidate_model_dirs():
    paths = []
    try:
        home = os.path.expanduser("~")
        local = os.getenv("LOCALAPPDATA") or os.path.join(home, "AppData", "Local")
        roaming = os.getenv("APPDATA") or os.path.join(home, "AppData", "Roaming")
        paths.extend([
            os.path.join(local, "LM Studio", "models"),
            os.path.join(roaming, "LM Studio", "models"),
            os.path.join(home, ".cache", "lm-studio", "models"),
            os.path.join(home, ".lmstudio", "models"),
            os.path.join(home, "Documents", "LM Studio", "models"),
        ])
        base = str(Path(__file__).resolve().parents[1])
        paths.extend([
            os.path.join(base, "LM Studio", "models"),
            os.path.join(base, "models"),
        ])
    except Exception:
        pass
    seen = set(); out = []
    for p in paths:
        p = os.path.normpath(p)
        if p not in seen:
            seen.add(p); out.append(p)
    return out

def _scan_models_fs(max_items=50):
    items = []
    try:
        for root in _candidate_model_dirs():
            if not os.path.isdir(root):
                continue
            for dirpath, dirnames, filenames in os.walk(root):
                ggufs = [f for f in filenames if f.lower().endswith('.gguf')]
                if ggufs:
                    name = os.path.basename(dirpath)
                    items.append({"id": name, "name": name, "description": ", ".join(ggufs[:3])})
                elif 'model.json' in filenames:
                    name = os.path.basename(dirpath)
                    items.append({"id": name, "name": name, "description": 'model.json'})
                if len(items) >= max_items:
                    return items
    except Exception:
        pass
    return items

def get_available_local_models():
    """Get local models via LM Studio API, with filesystem fallback."""
    try:
        # Defer import of LM_STUDIO_URL if present earlier in file
        url = os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1")
        r = requests.get(f"{url}/models", timeout=3)
        if r.ok:
            data = r.json() or {}
            items = []
            for m in (data.get("data") or []):
                mid = (m.get("id") or m.get("model") or "").strip()
                if not mid:
                    continue
                name = m.get("name") or mid
                items.append({
                    "id": mid,
                    "name": name,
                    "description": m.get("description", ""),
                    "size": m.get("size", ""),
                    "specialty": m.get("tags", "")
                })
            if items:
                return items
    except Exception:
        pass
    fs_items = _scan_models_fs()
    return fs_items