#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI-Powered DuckBot Ecosystem Manager
Integrates with LM Studio or OpenRouter for intelligent server management
"""

import os
import sys
import time
import json
import asyncio
import aiohttp
import threading
import requests
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import logging
from enum import Enum

# Import our enterprise ecosystem manager
from start_ecosystem import EcosystemManager, ServiceStatus, logger, perf_logger, security_logger

# Wrap imported loggers to tolerate malformed format calls
def _wrap_safe(level_method):
    def _safe(msg, *args, **kwargs):
        try:
            level_method(msg, *args, **kwargs)
        except Exception:
            try:
                level_method(" ".join(str(x) for x in (msg,) + args))
            except Exception:
                pass
    return _safe

try:
    logger.info = _wrap_safe(logger.info)
    logger.warning = _wrap_safe(logger.warning)
    logger.error = _wrap_safe(logger.error)
    logger.debug = _wrap_safe(logger.debug)
    perf_logger.info = _wrap_safe(perf_logger.info)
    security_logger.info = _wrap_safe(security_logger.info)
    security_logger.warning = _wrap_safe(security_logger.warning)
except Exception:
    pass

# Import caching system
from core_ai.ai_cache_manager import AICacheManager, CachedAPICall

@dataclass
class AIManagerConfig:
    provider: str = "lm_studio"  # "lm_studio" or "openrouter"
    lm_studio_url: str = "http://localhost:1234/v1"
    lm_studio_model: str = "openai/gpt-oss-20b"
    openrouter_api_key: str = ""
    openrouter_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "qwen/qwen3-coder:free"
    max_tokens: int = 1500
    temperature: float = 0.3
    conversation_history_limit: int = 50
    decision_confidence_threshold: float = 0.7
    auto_action_enabled: bool = True
    monitoring_interval: int = 30
    report_interval: int = 300  # 5 minutes
    enable_caching: bool = True
    cache_ttl_seconds: int = 300

class DecisionType(Enum):
    RESTART_SERVICE = "restart_service"
    SCALE_RESOURCES = "scale_resources"
    INVESTIGATE_ISSUE = "investigate_issue"
    OPTIMIZE_PERFORMANCE = "optimize_performance"
    SEND_ALERT = "send_alert"
    DO_NOTHING = "do_nothing"
    REQUEST_HUMAN_INTERVENTION = "request_human_intervention"

@dataclass
class AIDecision:
    decision_type: DecisionType
    confidence: float
    reasoning: str
    action_params: Dict[str, Any]
    estimated_impact: str
    risk_level: str  # "low", "medium", "high"

@dataclass
class SystemState:
    timestamp: datetime
    services_status: Dict[str, ServiceStatus]
    system_metrics: Dict[str, float]
    recent_events: List[Dict[str, Any]]
    error_patterns: List[str]
    performance_trends: Dict[str, List[float]]

class AIEcosystemManager(EcosystemManager):
    """AI-Enhanced Ecosystem Manager with intelligent decision making"""
    
    def __init__(self, ai_config: AIManagerConfig = None):
        super().__init__()
        
        self.ai_config = ai_config or AIManagerConfig()
        self.conversation_history: List[Dict[str, str]] = []
        self.decision_history: List[AIDecision] = []
        self.system_knowledge: Dict[str, Any] = {}
        self.ai_session = None
        self.last_ai_report = datetime.now()
        
        # Initialize caching system
        self.cache_manager = AICacheManager(self.base_dir / "ai_cache")
        
        # AI management state
        self.ai_monitoring_active = False
        self.ai_thread = None
        
        # Initialize AI configuration
        self.load_ai_config()
        
        logger.info("ðŸ¤– AI-Enhanced Ecosystem Manager initialized with caching")
        security_logger.info(f"AI Manager configured with provider: {self.ai_config.provider}")

    def load_ai_config(self):
        """Load AI configuration from file or environment"""
        config_file = self.base_dir / "ai_config.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                
                # Update configuration with loaded values
                for key, value in config_data.items():
                    if hasattr(self.ai_config, key):
                        setattr(self.ai_config, key, value)
                
                logger.info("âœ… AI configuration loaded from file")
                
            except Exception as e:
                logger.error(f"âŒ Failed to load AI config: {e}")
        
        # Override with environment variables
        env_mappings = {
            'AI_PROVIDER': 'provider',
            'LM_STUDIO_URL': 'lm_studio_url',
            'LM_STUDIO_MODEL': 'lm_studio_model',
            'OPENROUTER_API_KEY': 'openrouter_api_key',
            'OPENROUTER_MODEL': 'openrouter_model',
            'AI_AUTO_ACTION': 'auto_action_enabled',
            'AI_ENABLE_CACHING': 'enable_caching',
            'AI_CACHE_TTL': 'cache_ttl_seconds',
            'AI_MAX_TOKENS': 'max_tokens',
            'AI_TEMPERATURE': 'temperature'
        }
        
        for env_var, config_attr in env_mappings.items():
            if os.getenv(env_var):
                value = os.getenv(env_var)
                # Convert boolean strings
                if value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'
                setattr(self.ai_config, config_attr, value)
        
        # Save current configuration
        self.save_ai_config()

    def save_ai_config(self):
        """Save current AI configuration to file"""
        config_file = self.base_dir / "ai_config.json"
        try:
            with open(config_file, 'w') as f:
                json.dump(asdict(self.ai_config), f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save AI config: {e}")

    async def create_ai_session(self):
        """Create HTTP session for AI API calls"""
        if not self.ai_session:
            self.ai_session = aiohttp.ClientSession()
        return self.ai_session

    async def close_ai_session(self):
        """Close AI HTTP session"""
        if self.ai_session:
            await self.ai_session.close()
            self.ai_session = None

    def get_current_model(self) -> str:
        """Get the appropriate model based on provider"""
        if self.ai_config.provider == "lm_studio":
            return self.ai_config.lm_studio_model
        elif self.ai_config.provider == "openrouter":
            return self.ai_config.openrouter_model
        else:
            return "unknown-model"

    async def _pick_lm_studio_model(self, request_type: str = "general") -> Optional[str]:
        """Pick a concrete LM Studio model when set to auto-detect.
        Strategy: query /models and choose a sensible default.
        Preference order: coder/code â†’ instruct/chat â†’ first available.
        """
        try:
            session = await self.create_ai_session()
            url = f"{self.ai_config.lm_studio_url}/models"
            async with session.get(url, timeout=8) as resp:
                if resp.status != 200:
                    logger.warning(f"LM Studio /models returned {resp.status}")
                    return None
                data = await resp.json()
        except Exception as e:
            logger.warning(f"Failed to list LM Studio models: {e}")
            return None

        items = data.get("data") or data.get("models") or []
        if not items:
            logger.warning("LM Studio reports zero available models")
            return None

        # Normalize list of ids
        candidates = []
        for m in items:
            mid = m.get("id") or m.get("model") or m.get("name")
            if isinstance(mid, str):
                candidates.append(mid)

        if not candidates:
            return None

        # Heuristics by request type
        req = (request_type or "").lower()
        def pref_score(mid: str) -> int:
            s = mid.lower()
            score = 0
            # Strong preferences: high-quality reasoning models
            if any(k in s for k in ("nemotron", "ace", "reason")):
                score += 40
            if any(k in s for k in ("deepseek", "r1")):
                score += 30
            if "coder" in s or "code" in s:
                score += 20
            if any(k in s for k in ("instruct", "chat", "qwen", "llama", "gemma")):
                score += 10
            if req in ("code", "debug", "analysis") and ("coder" in s or "code" in s):
                score += 10
            return score

        chosen = sorted(candidates, key=pref_score, reverse=True)[0]
        logger.info(f"LM Studio auto-detected model: {chosen}")
        return chosen

    async def warm_up_lm_studio(self, request_type: str = "general") -> None:
        """Warm up LM Studio by selecting a model and sending a tiny request.
        This speeds up the first real call and ensures the model is resident.
        """
        if self.ai_config.provider != "lm_studio":
            return
        # Ensure model selected
        auto_vals = {"auto", "auto-detect", "auto_detect", "autodetect", ""}
        current = (self.ai_config.lm_studio_model or "").strip()
        if current.lower() in auto_vals:
            chosen = await self._pick_lm_studio_model(request_type)
            if chosen:
                self.ai_config.lm_studio_model = chosen

        # Post a tiny warm-up request
        try:
            session = await self.create_ai_session()
            url = f"{self.ai_config.lm_studio_url}/chat/completions"
            payload = {
                "model": self.ai_config.lm_studio_model,
                "messages": [
                    {"role": "system", "content": "warmup"},
                    {"role": "user", "content": "ping"}
                ],
                "max_tokens": 1,
                "temperature": 0.0,
                "stream": False
            }
            async with session.post(url, json=payload, timeout=20) as resp:
                if resp.status == 200:
                    logger.info("LM Studio warm-up completed")
                else:
                    logger.warning(f"LM Studio warm-up status: {resp.status}")
        except Exception as e:
            logger.warning(f"LM Studio warm-up failed: {e}")

    async def check_lm_studio_health(self) -> bool:
        """Check if LM Studio is available and responsive"""
        if self.ai_config.provider != "lm_studio":
            return True  # Not using LM Studio, so it's "healthy" for our purposes
        
        try:
            session = await self.create_ai_session()
            url = f"{self.ai_config.lm_studio_url}/health"
            
            # Try health endpoint first
            async with session.get(url, timeout=5) as response:
                if response.status == 200:
                    logger.debug("âœ… LM Studio health check passed")
                    return True
        except Exception:
            # If health endpoint fails, try a simple models list
            try:
                url = f"{self.ai_config.lm_studio_url}/models"
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        logger.debug("âœ… LM Studio models endpoint responsive")
                        return True
            except Exception:
                pass
        
        logger.warning("LM Studio not available or not responding")
        return False

    def fallback_to_openrouter(self):
        """Switch to OpenRouter as fallback provider"""
        if not self.ai_config.openrouter_api_key:
            logger.error("âŒ Cannot fallback to OpenRouter: No API key configured")
            return False
        
        # Track original provider for restore capability
        if not hasattr(self, '_original_provider'):
            self._original_provider = self.ai_config.provider
        
        logger.warning("ðŸ”„ Falling back to OpenRouter due to LM Studio unavailability")
        self.ai_config.provider = "openrouter"
        self.get_conservative_rate_limits()  # Update rate limits for OpenRouter
        return True

    async def attempt_restore_lm_studio(self, original_provider: str):
        """Attempt to restore LM Studio as primary provider"""
        if original_provider != "lm_studio":
            return  # Only restore if LM Studio was the original provider
        
        # Don't check too frequently - only check every few minutes
        current_time = time.time()
        if not hasattr(self, '_last_restore_check'):
            self._last_restore_check = 0
        
        if current_time - self._last_restore_check < 180:  # 3 minutes
            return
        
        self._last_restore_check = current_time
        
        # Check if LM Studio is now available
        temp_provider = self.ai_config.provider
        self.ai_config.provider = "lm_studio"  # Temporarily switch back to check
        
        if await self.check_lm_studio_health():
            logger.info("âœ… LM Studio is available again - restoring as primary provider")
            self.get_conservative_rate_limits()  # Update rate limits for LM Studio
            security_logger.info("AI Provider restored from OpenRouter back to LM Studio")
            # Clear the original provider tracking since we've restored
            if hasattr(self, '_original_provider'):
                delattr(self, '_original_provider')
        else:
            # Restore the fallback provider
            self.ai_config.provider = temp_provider

    def get_conservative_rate_limits(self):
        """Set rate limits based on provider and tier"""
        if self.ai_config.provider == "openrouter":
            # Conservative limits for OpenRouter higher free tier
            # These limits respect the free tier caps while allowing proper functionality
            self.cache_manager.rate_limits.requests_per_minute = 12   # Higher free tier allows more
            self.cache_manager.rate_limits.requests_per_hour = 200    # ~3-4 per minute average
            self.cache_manager.rate_limits.requests_per_day = 2000    # Conservative daily limit
            self.cache_manager.rate_limits.tokens_per_minute = 20000  # Higher token allowance
            
            logger.info(f"ðŸ”„ OpenRouter rate limits: 12/min, 200/hour, 2000/day (higher free tier)")
        else:
            # More relaxed for LM Studio (local)
            self.cache_manager.rate_limits.requests_per_minute = 20
            self.cache_manager.rate_limits.requests_per_hour = 500
            self.cache_manager.rate_limits.requests_per_day = 5000
            
            logger.info(f"ðŸ  LM Studio rate limits: 20/min, 500/hour, 5000/day (local)")

    async def call_ai_api(self, messages: List[Dict[str, str]], request_type: str = "general", max_retries: int = 3) -> Optional[str]:
        """Make cached API call to LM Studio or OpenRouter with automatic fallback"""
        
        original_provider = self.ai_config.provider
        
        # Check LM Studio health if it's the primary provider
        if original_provider == "lm_studio":
            if not await self.check_lm_studio_health():
                if not self.fallback_to_openrouter():
                    logger.error("âŒ Both LM Studio and OpenRouter fallback failed")
                    return None
                else:
                    security_logger.warning("AI Provider switched from LM Studio to OpenRouter (fallback)")
        
        # Set conservative rate limits based on current provider
        self.get_conservative_rate_limits()
        
        # Resolve LM Studio model if auto-detect is requested
        if self.ai_config.provider == "lm_studio":
            auto_vals = {"auto", "auto-detect", "auto_detect", "autodetect", ""}
            current = (self.ai_config.lm_studio_model or "").strip()
            if current.lower() in auto_vals:
                chosen = await self._pick_lm_studio_model(request_type)
                if not chosen:
                    logger.error("No LM Studio model available to select")
                    return None
                self.ai_config.lm_studio_model = chosen

        # Prepare request configuration
        config = {
            "model": self.get_current_model(),
            "max_tokens": self.ai_config.max_tokens,
            "temperature": self.ai_config.temperature
        }
        
        # Use caching if enabled
        try:
            if self.ai_config.enable_caching:
                with CachedAPICall(
                    cache_manager=self.cache_manager,
                    provider=self.ai_config.provider,
                    model=config["model"],
                    request_type=request_type,
                    use_cache=True
                ) as cached_call:
                    
                    def make_api_request():
                        return asyncio.run(self._make_actual_api_call(messages, config, max_retries))
                    
                    try:
                        response, from_cache = cached_call.get_cached_or_call(messages, config, make_api_request)
                        
                        if from_cache:
                            logger.debug(f"ðŸŽ¯ Using cached response for {request_type}")
                        else:
                            logger.debug(f"ðŸŒ API call made for {request_type} via {self.ai_config.provider}")
                        
                        # If we successfully got a response and were using fallback, 
                        # check if we can restore primary provider
                        if response and original_provider == "lm_studio" and self.ai_config.provider == "openrouter":
                            await self.attempt_restore_lm_studio(original_provider)
                        
                        return response
                        
                    except Exception as e:
                        if "Rate limit exceeded" in str(e):
                            logger.warning(f"ðŸš¦ Rate limit hit on {self.ai_config.provider}, waiting before retry...")
                            await asyncio.sleep(60)  # Wait 1 minute
                            return None
                        else:
                            logger.error(f"âŒ Cached API call failed on {self.ai_config.provider}: {e}")
                            return None
            else:
                # Direct API call without caching
                response = await self._make_actual_api_call(messages, config, max_retries)
                
                # Check for restore opportunity
                if response and original_provider == "lm_studio" and self.ai_config.provider == "openrouter":
                    await self.attempt_restore_lm_studio(original_provider)
                
                return response
                
        except Exception as e:
            logger.error(f"âŒ API call failed completely: {e}")
            return None

    async def _make_actual_api_call(self, messages: List[Dict[str, str]], config: Dict, max_retries: int) -> Optional[str]:
        """Make the actual API call without caching layer"""
        session = await self.create_ai_session()
        
        # Prepare request based on provider
        if self.ai_config.provider == "lm_studio":
            url = f"{self.ai_config.lm_studio_url}/chat/completions"
            headers = {"Content-Type": "application/json"}
            
        elif self.ai_config.provider == "openrouter":
            url = f"{self.ai_config.openrouter_url}/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.ai_config.openrouter_api_key}",
                "HTTP-Referer": "https://github.com/DuckBot-AI/ecosystem-manager",
                "X-Title": "DuckBot AI Ecosystem Manager"
            }
        else:
            logger.error(f"âŒ Unsupported AI provider: {self.ai_config.provider}")
            return None
        
        payload = {
            "model": config["model"],
            "messages": messages,
            "max_tokens": config["max_tokens"],
            "temperature": config["temperature"],
            "stream": False
        }
        
        # Add provider-specific parameters for OpenRouter
        if self.ai_config.provider == "openrouter":
            payload.update({
                "route": "fallback",
                "models": [config["model"]]  # Specify exact model
            })
        
        # Retry logic with longer delays for OpenRouter
        base_delay = 5 if self.ai_config.provider == "openrouter" else 2
        
        for attempt in range(max_retries):
            try:
                # Add extra delay for OpenRouter to respect rate limits
                if attempt > 0 and self.ai_config.provider == "openrouter":
                    await asyncio.sleep(base_delay * (2 ** attempt))
                
                timeout = 45 if self.ai_config.provider == "openrouter" else 30
                
                async with session.post(url, json=payload, headers=headers, timeout=timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if 'choices' in data and len(data['choices']) > 0:
                            content = data['choices'][0]['message']['content']
                            
                            # Log successful API call with provider info
                            perf_logger.info(f"AI API success: {self.ai_config.provider} ({attempt + 1}/{max_retries})")
                            return content.strip()
                        else:
                            logger.warning("âš ï¸ No choices in AI response")
                    
                    elif response.status == 429:
                        # Rate limit hit
                        logger.warning(f"ðŸš¦ Rate limit hit on {self.ai_config.provider}")
                        if attempt < max_retries - 1:
                            wait_time = 60 * (attempt + 1)  # Progressive backoff
                            logger.info(f"â³ Waiting {wait_time}s before retry...")
                            await asyncio.sleep(wait_time)
                            continue
                    
                    else:
                        error_text = await response.text()
                        logger.warning(f"âš ï¸ AI API error {response.status}: {error_text}")
                        
            except asyncio.TimeoutError:
                logger.warning(f"âš ï¸ AI API timeout (attempt {attempt + 1})")
            except Exception as e:
                logger.error(f"âŒ AI API error (attempt {attempt + 1}): {e}")
            
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
        
        logger.error(f"âŒ Failed to get AI response after {max_retries} attempts")
        return None

    def get_system_state(self) -> SystemState:
        """Gather current system state for AI analysis"""
        
        # Get current service statuses
        services_status = {}
        for service_name in self.services.keys():
            services_status[service_name] = self.service_status.get(service_name, ServiceStatus.STOPPED)
        
        # Get system metrics
        try:
            import psutil
            system_metrics = {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent if sys.platform != "win32" else psutil.disk_usage('C:/').percent,
                'uptime_hours': (datetime.now() - self.start_time).total_seconds() / 3600
            }
        except ImportError:
            logger.warning("psutil not available - system metrics will be limited")
            system_metrics = {'uptime_hours': (datetime.now() - self.start_time).total_seconds() / 3600}
        except Exception as e:
            logger.warning(f"Could not gather system metrics: {e}")
            system_metrics = {}
        
        # Get recent events from database
        recent_events = []
        try:
            import sqlite3
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT * FROM service_history WHERE timestamp > datetime('now', '-1 hour') ORDER BY timestamp DESC LIMIT 20"
                )
                recent_events = [
                    {
                        'service': row[1],
                        'status': row[2], 
                        'timestamp': row[3],
                        'details': row[4]
                    }
                    for row in cursor.fetchall()
                ]
        except Exception as e:
            logger.warning(f"Could not fetch recent events: {e}")
        
        # Analyze error patterns
        error_patterns = []
        failed_services = [name for name, status in services_status.items() if status == ServiceStatus.FAILED]
        if failed_services:
            error_patterns.append(f"Failed services: {', '.join(failed_services)}")
        
        # Get performance trends
        performance_trends = {}
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT service_name, metric_name, AVG(metric_value) as avg_value FROM performance_metrics WHERE timestamp > datetime('now', '-1 hour') GROUP BY service_name, metric_name"
                )
                for row in cursor.fetchall():
                    service, metric, avg_value = row
                    if service not in performance_trends:
                        performance_trends[service] = {}
                    performance_trends[service][metric] = avg_value
        except Exception as e:
            logger.warning(f"Could not fetch performance trends: {e}")
        
        return SystemState(
            timestamp=datetime.now(),
            services_status=services_status,
            system_metrics=system_metrics,
            recent_events=recent_events,
            error_patterns=error_patterns,
            performance_trends=performance_trends
        )

    def create_system_prompt(self) -> str:
        """Create system prompt for AI ecosystem manager"""
        return """You are an AI-powered ecosystem manager for the DuckBot system. Your role is to:

1. MONITOR: Continuously analyze system health, performance metrics, and service status
2. DIAGNOSE: Identify issues, patterns, and potential problems before they become critical
3. DECIDE: Make intelligent decisions about service management, restarts, and optimizations
4. ACT: Execute approved actions to maintain system stability and performance
5. COMMUNICATE: Provide clear, actionable insights and status reports

ECOSYSTEM OVERVIEW:
- ComfyUI: Image/video generation service (critical)
- DuckBot: Discord bot (critical) 
- n8n: Workflow automation (important)
- Open Notebook: AI notebook interface (optional)
- Jupyter: Data analysis platform (optional)

DECISION FRAMEWORK:
- Always prioritize system stability and user experience
- Consider resource usage, error rates, and response times
- Escalate to humans for high-risk decisions
- Maintain detailed reasoning for all actions
- Be proactive but conservative with critical services

RESPONSE FORMAT:
Always respond in JSON format with these fields:
{
  "analysis": "Brief analysis of current situation",
  "decision_type": "restart_service|scale_resources|investigate_issue|optimize_performance|send_alert|do_nothing|request_human_intervention",
  "confidence": 0.0-1.0,
  "reasoning": "Detailed explanation of decision",
  "action_params": {"service_name": "...", "reason": "..."},
  "estimated_impact": "Expected outcome",
  "risk_level": "low|medium|high",
  "human_message": "Optional message for human operators"
}

Be concise, accurate, and always err on the side of caution for critical services."""

    async def analyze_and_decide(self, system_state: SystemState) -> Optional[AIDecision]:
        """Analyze system state and make management decisions"""
        
        # Create context for AI
        context = {
            "current_time": system_state.timestamp.isoformat(),
            "services": {name: status.value for name, status in system_state.services_status.items()},
            "system_metrics": system_state.system_metrics,
            "recent_events": system_state.recent_events[-10:],  # Last 10 events
            "error_patterns": system_state.error_patterns,
            "performance_trends": system_state.performance_trends,
            "restart_counts": {k: v for k, v in self.restart_counts.items() if v > 0}
        }
        
        # Build conversation
        messages = [
            {"role": "system", "content": self.create_system_prompt()},
            {"role": "user", "content": f"Analyze the current system state and recommend an action:\n\n{json.dumps(context, indent=2)}"}
        ]
        
        # Add recent conversation context
        for msg in self.conversation_history[-5:]:  # Last 5 exchanges
            messages.append(msg)
        
        try:
            # Get AI response with decision_making cache type
            ai_response = await self.call_ai_api(messages, request_type="decision_making")
            if not ai_response:
                return None
            
            # Log the conversation
            self.conversation_history.append({"role": "user", "content": f"System analysis request at {system_state.timestamp}"})
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            
            # Keep conversation history manageable
            if len(self.conversation_history) > self.ai_config.conversation_history_limit:
                self.conversation_history = self.conversation_history[-self.ai_config.conversation_history_limit:]
            
            # Parse AI decision
            try:
                decision_data = json.loads(ai_response)
                
                decision = AIDecision(
                    decision_type=DecisionType(decision_data.get('decision_type', 'do_nothing')),
                    confidence=float(decision_data.get('confidence', 0.0)),
                    reasoning=decision_data.get('reasoning', 'No reasoning provided'),
                    action_params=decision_data.get('action_params', {}),
                    estimated_impact=decision_data.get('estimated_impact', 'Unknown impact'),
                    risk_level=decision_data.get('risk_level', 'medium')
                )
                
                # Log the decision
                logger.info(f"ðŸ¤– AI Decision: {decision.decision_type.value} (confidence: {decision.confidence:.2f})")
                logger.info(f"ðŸ¤– Reasoning: {decision.reasoning}")
                
                # Add to decision history
                self.decision_history.append(decision)
                if len(self.decision_history) > 100:
                    self.decision_history = self.decision_history[-100:]
                
                return decision
                
            except json.JSONDecodeError as e:
                logger.error(f"âŒ Failed to parse AI response as JSON: {e}")
                logger.error(f"Raw AI response: {ai_response}")
                return None
            except ValueError as e:
                logger.error(f"âŒ Invalid decision type in AI response: {e}")
                return None
                
        except Exception as e:
            logger.error(f"âŒ Error in AI analysis: {e}")
            return None

    async def execute_decision(self, decision: AIDecision) -> bool:
        """Execute an AI decision with appropriate safeguards"""
        
        # Check if auto-action is enabled
        if not self.ai_config.auto_action_enabled and decision.decision_type != DecisionType.DO_NOTHING:
            logger.info(f"ðŸ¤– AI recommends {decision.decision_type.value} but auto-action is disabled")
            return False
        
        # Check confidence threshold
        if decision.confidence < self.ai_config.decision_confidence_threshold:
            logger.info(f"ðŸ¤– Decision confidence {decision.confidence:.2f} below threshold {self.ai_config.decision_confidence_threshold}")
            return False
        
        # Check risk level
        if decision.risk_level == "high":
            logger.warning(f"ðŸ¤– High-risk decision detected, requesting human approval: {decision.reasoning}")
            security_logger.warning(f"AI requested high-risk action: {decision.decision_type.value}")
            return False
        
        try:
            # Execute based on decision type
            if decision.decision_type == DecisionType.RESTART_SERVICE:
                service_name = decision.action_params.get('service_name')
                if service_name and service_name in self.services:
                    logger.info(f"ðŸ¤– AI executing service restart: {service_name}")
                    self.restart_service(service_name)
                    return True
                    
            elif decision.decision_type == DecisionType.INVESTIGATE_ISSUE:
                # Log investigation request
                logger.info(f"ðŸ¤– AI investigation: {decision.reasoning}")
                # Could trigger additional monitoring or diagnostics
                return True
                
            elif decision.decision_type == DecisionType.SEND_ALERT:
                logger.warning(f"ðŸ¤– AI Alert: {decision.reasoning}")
                security_logger.warning(f"AI Alert: {decision.reasoning}")
                return True
                
            elif decision.decision_type == DecisionType.DO_NOTHING:
                logger.debug("ðŸ¤– AI decision: No action required")
                return True
                
            elif decision.decision_type == DecisionType.REQUEST_HUMAN_INTERVENTION:
                logger.critical(f"ðŸ¤– AI requests human intervention: {decision.reasoning}")
                security_logger.critical(f"AI requests human intervention: {decision.reasoning}")
                return True
                
            else:
                logger.warning(f"ðŸ¤– Unhandled decision type: {decision.decision_type.value}")
                return False
                
        except Exception as e:
            logger.error(f"âŒ Failed to execute AI decision: {e}")
            return False

    async def ai_monitoring_loop(self):
        """Main AI monitoring and management loop"""
        logger.info("ðŸ¤– Starting AI monitoring loop...")
        
        while not self.shutdown_requested and self.ai_monitoring_active:
            try:
                # Get current system state
                system_state = self.get_system_state()
                
                # Analyze and make decision
                decision = await self.analyze_and_decide(system_state)
                
                if decision:
                    # Execute decision
                    success = await self.execute_decision(decision)
                    
                    if success:
                        perf_logger.info(f"AI action executed: {decision.decision_type.value}")
                    else:
                        logger.warning(f"AI action blocked or failed: {decision.decision_type.value}")
                
                # Generate periodic reports
                if (datetime.now() - self.last_ai_report).total_seconds() > self.ai_config.report_interval:
                    await self.generate_ai_report()
                    self.last_ai_report = datetime.now()
                
                # Wait for next monitoring cycle
                await asyncio.sleep(self.ai_config.monitoring_interval)
                
            except Exception as e:
                logger.error(f"âŒ Error in AI monitoring loop: {e}")
                await asyncio.sleep(30)  # Back off on error

    async def generate_ai_report(self):
        """Generate periodic AI status report"""
        try:
            system_state = self.get_system_state()
            
            # Create report request
            messages = [
                {"role": "system", "content": "Generate a concise status report about the DuckBot ecosystem. Include system health, recent actions, and any recommendations. Keep it under 200 words."},
                {"role": "user", "content": f"Current system state:\n{json.dumps(asdict(system_state), default=str, indent=2)}"}
            ]
            
            report = await self.call_ai_api(messages, request_type="reports")
            if report:
                logger.info(f"ðŸ¤– AI Status Report:\n{report}")
                
                # Could save to file or send to Discord/email
                report_file = self.base_dir / "logs" / f"ai_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                report_file.parent.mkdir(exist_ok=True)
                
                with open(report_file, 'w') as f:
                    f.write(f"AI Ecosystem Report - {datetime.now()}\n")
                    f.write("=" * 50 + "\n")
                    f.write(report)
                
        except Exception as e:
            logger.error(f"Failed to generate AI report: {e}")

    def start_ai_management(self):
        """Start AI-powered management"""
        if self.ai_monitoring_active:
            logger.warning("AI management already active")
            return
        
        self.ai_monitoring_active = True
        
        # Start AI monitoring in separate thread
        def run_ai_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.ai_monitoring_loop())
            finally:
                loop.run_until_complete(self.close_ai_session())
                loop.close()
        
        self.ai_thread = threading.Thread(target=run_ai_loop, daemon=True)
        self.ai_thread.start()
        
        logger.info("ðŸ¤– AI management started")

    def stop_ai_management(self):
        """Stop AI-powered management"""
        self.ai_monitoring_active = False
        
        if self.ai_thread:
            self.ai_thread.join(timeout=10)
        
        logger.info("ðŸ¤– AI management stopped")

    async def chat_with_ai(self, user_message: str) -> str:
        """Interactive chat interface with AI manager"""
        system_state = self.get_system_state()
        
        messages = [
            {"role": "system", "content": "You are the AI ecosystem manager. The user is asking you a question. Provide a helpful, informative response based on the current system state. Keep responses conversational and under 300 words."},
            {"role": "user", "content": f"Current system: {json.dumps(asdict(system_state), default=str)}\n\nUser question: {user_message}"}
        ]
        
        # Add conversation context
        for msg in self.conversation_history[-5:]:
            messages.append(msg)
        
        response = await self.call_ai_api(messages, request_type="general_chat")
        
        if response:
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": response})
        
        return response or "Sorry, I'm having trouble processing your request right now."

    def print_ai_status(self):
        """Print AI management status"""
        print("\n" + "="*60)
        print("ðŸ¤– AI ECOSYSTEM MANAGER STATUS")
        print("="*60)
        
        print(f"Provider: {self.ai_config.provider}")
        print(f"Model: {self.get_current_model()}")
        print(f"Auto-actions: {'âœ… Enabled' if self.ai_config.auto_action_enabled else 'âŒ Disabled'}")
        print(f"Monitoring: {'âœ… Active' if self.ai_monitoring_active else 'âŒ Inactive'}")
        print(f"Caching: {'âœ… Enabled' if self.ai_config.enable_caching else 'âŒ Disabled'}")
        print(f"Decisions made: {len(self.decision_history)}")
        print(f"Confidence threshold: {self.ai_config.decision_confidence_threshold}")
        
        # Show fallback status
        if hasattr(self, '_original_provider'):
            print(f"âš ï¸ Fallback: Using {self.ai_config.provider} (primary: {self._original_provider} unavailable)")
        
        if self.decision_history:
            recent_decision = self.decision_history[-1]
            print(f"Last decision: {recent_decision.decision_type.value} (confidence: {recent_decision.confidence:.2f})")
        
        # Show cache stats if available
        try:
            cache_stats = self.cache_manager.get_cache_stats()
            if cache_stats.get('total_cache_hits', 0) > 0:
                print(f"Cache hits: {cache_stats.get('total_cache_hits', 0)}")
                print(f"Cache entries: {cache_stats.get('total_cache_entries', 0)}")
        except Exception:
            pass
        
        print("="*60 + "\n")

    def run(self):
        """Enhanced run method with AI management"""
        # Run the base ecosystem startup
        success = super().run()
        
        if success and not self.shutdown_requested:
            # Start AI management
            self.start_ai_management()
            
            # Enhanced status display
            self.print_ai_status()
            
            logger.info("ðŸ¤– AI-Enhanced Ecosystem ready")
        
        return success

    def shutdown_all(self):
        """Enhanced shutdown with AI management cleanup"""
        # Stop AI management first
        self.stop_ai_management()
        
        # Run base shutdown
        super().shutdown_all()

# Interactive CLI for AI management
async def interactive_ai_chat():
    """Interactive chat interface with AI manager"""
    print("\nðŸ¤– AI Ecosystem Manager Chat Interface")
    print("Type 'exit' to quit, 'status' for system status")
    print("-" * 50)
    
    # This would need to be connected to a running AI manager instance
    # For now, just a placeholder
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                break
            elif user_input.lower() == 'status':
                print("ðŸ“Š System status would be displayed here")
            else:
                print("ðŸ¤– AI: This is a placeholder. Connect to running AI manager for real responses.")
                
        except KeyboardInterrupt:
            break
    
    print("\nGoodbye! ðŸ‘‹")

if __name__ == "__main__":
    # Command line interface
    import argparse
    
    parser = argparse.ArgumentParser(description="AI-Enhanced DuckBot Ecosystem Manager")
    parser.add_argument('--chat', action='store_true', help='Start interactive chat interface')
    parser.add_argument('--provider', choices=['lm_studio', 'openrouter'], default='lm_studio', help='AI provider')
    parser.add_argument('--model', default='local-model', help='Model name')
    parser.add_argument('--no-auto-action', action='store_true', help='Disable automatic actions')
    
    args = parser.parse_args()
    
    if args.chat:
        asyncio.run(interactive_ai_chat())
    else:
        # Create AI configuration
        ai_config = AIManagerConfig(
            provider=args.provider,
            lm_studio_model=args.model if args.provider == "lm_studio" else "openai/gpt-oss-20b",
            openrouter_model=args.model if args.provider == "openrouter" else "qwen/qwen3-coder:free",
            auto_action_enabled=not args.no_auto_action
        )
        
        # Start AI-enhanced ecosystem manager
        try:
            manager = AIEcosystemManager(ai_config)
            success = manager.run()
            sys.exit(0 if success else 1)
        except Exception as e:
            logger.critical(f"ðŸ’¥ Fatal error: {e}")
            sys.exit(1)
