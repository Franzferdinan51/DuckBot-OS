#!/usr/bin/env python3
"""
DuckBot Cost Tracking System
Monitors API costs, token usage, and provides cost predictions
"""

import json
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict, field
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class ModelPricing:
    """Pricing information for AI models"""
    provider: str
    model: str
    input_cost_per_1k: float  # Cost per 1K input tokens
    output_cost_per_1k: float  # Cost per 1K output tokens
    is_free: bool = False
    free_tier_limit: Optional[int] = None  # Tokens per month/day
    reset_period: str = "monthly"  # daily, monthly, yearly

@dataclass 
class UsageRecord:
    """Individual API usage record"""
    timestamp: datetime
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    total_cost: float
    request_type: str  # chat, completion, etc.
    user_id: Optional[str] = None
    session_id: Optional[str] = None

@dataclass
class CostSummary:
    """Cost summary for a time period"""
    total_cost: float = 0.0
    total_tokens: int = 0
    total_requests: int = 0
    by_provider: Dict[str, float] = field(default_factory=dict)
    by_model: Dict[str, float] = field(default_factory=dict)
    projected_monthly: float = 0.0
    free_tier_usage: Dict[str, int] = field(default_factory=dict)

class CostTracker:
    """
    Comprehensive cost tracking system for AI API usage
    """
    
    # Model pricing database (updated regularly)
    MODEL_PRICING = {
        # OpenRouter Free Models
        "qwen/qwen3-coder:free": ModelPricing("openrouter", "qwen/qwen3-coder:free", 0.0, 0.0, True, 100000, "monthly"),
        "deepseek/deepseek-r1-0528:free": ModelPricing("openrouter", "deepseek/deepseek-r1-0528:free", 0.0, 0.0, True, 50000, "monthly"),
        "google/gemini-flash-1.5:free": ModelPricing("openrouter", "google/gemini-flash-1.5:free", 0.0, 0.0, True, 1000000, "monthly"),
        
        # OpenRouter Paid Models
        "anthropic/claude-3.5-sonnet": ModelPricing("openrouter", "anthropic/claude-3.5-sonnet", 3.0, 15.0),
        "openai/gpt-4o": ModelPricing("openrouter", "openai/gpt-4o", 2.5, 10.0),
        "openai/gpt-4o-mini": ModelPricing("openrouter", "openai/gpt-4o-mini", 0.15, 0.6),
        "google/gemini-pro-1.5": ModelPricing("openrouter", "google/gemini-pro-1.5", 1.25, 5.0),
        "anthropic/claude-3-haiku": ModelPricing("openrouter", "anthropic/claude-3-haiku", 0.25, 1.25),
        
        # OpenAI Direct
        "gpt-4o": ModelPricing("openai", "gpt-4o", 2.5, 10.0),
        "gpt-4o-mini": ModelPricing("openai", "gpt-4o-mini", 0.15, 0.6),
        "gpt-4-turbo": ModelPricing("openai", "gpt-4-turbo", 10.0, 30.0),
        "gpt-3.5-turbo": ModelPricing("openai", "gpt-3.5-turbo", 0.5, 1.5),
        
        # Anthropic Direct
        "claude-3-5-sonnet-20241022": ModelPricing("anthropic", "claude-3-5-sonnet-20241022", 3.0, 15.0),
        "claude-3-haiku-20240307": ModelPricing("anthropic", "claude-3-haiku-20240307", 0.25, 1.25),
        
        # LM Studio (Local - no cost)
        "local-model": ModelPricing("lm_studio", "local-model", 0.0, 0.0, True),
        
        # Groq (Free tier)
        "llama-3.1-70b-versatile": ModelPricing("groq", "llama-3.1-70b-versatile", 0.0, 0.0, True, 6000, "daily"),
        "mixtral-8x7b-32768": ModelPricing("groq", "mixtral-8x7b-32768", 0.0, 0.0, True, 5000, "daily"),
    }
    
    def __init__(self, db_path: str = "cost_tracking.db"):
        self.db_path = Path(db_path)
        self.lock = threading.RLock()
        self._init_database()
        
    def _init_database(self):
        """Initialize SQLite database for cost tracking"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS usage_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    input_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    total_cost REAL NOT NULL,
                    request_type TEXT NOT NULL,
                    user_id TEXT,
                    session_id TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_summaries (
                    date TEXT PRIMARY KEY,
                    total_cost REAL NOT NULL,
                    total_tokens INTEGER NOT NULL,
                    total_requests INTEGER NOT NULL,
                    summary_data TEXT NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON usage_records(timestamp);
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_provider_model ON usage_records(provider, model);
            """)
            
    def track_usage(self, 
                   provider: str, 
                   model: str, 
                   input_tokens: int, 
                   output_tokens: int,
                   request_type: str = "chat",
                   user_id: Optional[str] = None,
                   session_id: Optional[str] = None) -> float:
        """
        Track API usage and calculate cost
        
        Returns:
            float: Cost for this request
        """
        with self.lock:
            # Get model pricing
            pricing = self.MODEL_PRICING.get(model)
            if not pricing:
                # Try to find by provider + partial match
                for key, p in self.MODEL_PRICING.items():
                    if p.provider == provider and model in key:
                        pricing = p
                        break
            
            if not pricing:
                logger.warning(f"No pricing data for {provider}:{model}, assuming free")
                pricing = ModelPricing(provider, model, 0.0, 0.0, True)
            
            # Calculate cost
            input_cost = (input_tokens / 1000) * pricing.input_cost_per_1k
            output_cost = (output_tokens / 1000) * pricing.output_cost_per_1k
            total_cost = input_cost + output_cost
            
            # Create usage record
            record = UsageRecord(
                timestamp=datetime.now(),
                provider=provider,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_cost=total_cost,
                request_type=request_type,
                user_id=user_id,
                session_id=session_id
            )
            
            # Save to database
            self._save_usage_record(record)
            
            return total_cost
    
    def _save_usage_record(self, record: UsageRecord):
        """Save usage record to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO usage_records 
                (timestamp, provider, model, input_tokens, output_tokens, 
                 total_cost, request_type, user_id, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.timestamp.isoformat(),
                record.provider,
                record.model,
                record.input_tokens,
                record.output_tokens,
                record.total_cost,
                record.request_type,
                record.user_id,
                record.session_id
            ))
            
    def get_usage_summary(self, 
                         days: int = 30,
                         provider: Optional[str] = None,
                         model: Optional[str] = None) -> CostSummary:
        """
        Get usage summary for specified period
        
        Args:
            days: Number of days to look back
            provider: Filter by provider
            model: Filter by specific model
        """
        with self.lock:
            start_date = datetime.now() - timedelta(days=days)
            
            query = """
                SELECT provider, model, 
                       SUM(input_tokens + output_tokens) as total_tokens,
                       SUM(total_cost) as total_cost,
                       COUNT(*) as request_count,
                       SUM(input_tokens) as input_tokens,
                       SUM(output_tokens) as output_tokens
                FROM usage_records 
                WHERE timestamp >= ?
            """
            params = [start_date.isoformat()]
            
            if provider:
                query += " AND provider = ?"
                params.append(provider)
            if model:
                query += " AND model = ?"
                params.append(model)
                
            query += " GROUP BY provider, model"
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                summary = CostSummary()
                
                for row in rows:
                    prov, mod, tokens, cost, requests, inp_tokens, out_tokens = row
                    
                    summary.total_cost += cost
                    summary.total_tokens += tokens
                    summary.total_requests += requests
                    
                    # By provider
                    if prov not in summary.by_provider:
                        summary.by_provider[prov] = 0.0
                    summary.by_provider[prov] += cost
                    
                    # By model
                    if mod not in summary.by_model:
                        summary.by_model[mod] = 0.0
                    summary.by_model[mod] += cost
                    
                    # Track free tier usage
                    pricing = self.MODEL_PRICING.get(mod)
                    if pricing and pricing.is_free:
                        if mod not in summary.free_tier_usage:
                            summary.free_tier_usage[mod] = 0
                        summary.free_tier_usage[mod] += tokens
                
                # Calculate monthly projection
                if days > 0:
                    daily_avg = summary.total_cost / days
                    summary.projected_monthly = daily_avg * 30
                
                return summary
    
    def get_cost_predictions(self) -> Dict[str, Any]:
        """
        Generate cost predictions and comparisons
        """
        with self.lock:
            # Get current usage patterns
            summary_7d = self.get_usage_summary(days=7)
            summary_30d = self.get_usage_summary(days=30)
            
            predictions = {
                "current_trends": {
                    "daily_avg_cost": summary_7d.total_cost / 7,
                    "weekly_avg_cost": summary_7d.total_cost,
                    "monthly_projected": summary_7d.projected_monthly,
                    "quarterly_projected": summary_7d.projected_monthly * 3,
                    "yearly_projected": summary_7d.projected_monthly * 12,
                },
                "token_efficiency": {},
                "cost_comparisons": {},
                "free_tier_status": {},
                "recommendations": []
            }
            
            # Token efficiency by model
            for model, cost in summary_30d.by_model.items():
                if model in summary_30d.free_tier_usage:
                    tokens = summary_30d.free_tier_usage[model]
                else:
                    # Get token count from database
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.execute("""
                            SELECT SUM(input_tokens + output_tokens) 
                            FROM usage_records 
                            WHERE model = ? AND timestamp >= ?
                        """, (model, (datetime.now() - timedelta(days=30)).isoformat()))
                        result = cursor.fetchone()
                        tokens = result[0] if result[0] else 0
                
                if tokens > 0:
                    cost_per_1k = (cost / tokens) * 1000
                    predictions["token_efficiency"][model] = {
                        "cost_per_1k_tokens": cost_per_1k,
                        "total_tokens": tokens,
                        "total_cost": cost
                    }
            
            # Free tier status
            for model, usage in summary_30d.free_tier_usage.items():
                pricing = self.MODEL_PRICING.get(model)
                if pricing and pricing.is_free and pricing.free_tier_limit:
                    usage_percent = (usage / pricing.free_tier_limit) * 100
                    predictions["free_tier_status"][model] = {
                        "usage": usage,
                        "limit": pricing.free_tier_limit,
                        "usage_percent": usage_percent,
                        "reset_period": pricing.reset_period,
                        "estimated_paid_cost": self._estimate_paid_cost(model, usage)
                    }
            
            # Cost comparisons - what would it cost on paid models?
            total_tokens = summary_30d.total_tokens
            if total_tokens > 0:
                for model, pricing in self.MODEL_PRICING.items():
                    if not pricing.is_free:
                        # Estimate 60/40 input/output split
                        est_input = int(total_tokens * 0.6)
                        est_output = int(total_tokens * 0.4)
                        est_cost = ((est_input / 1000) * pricing.input_cost_per_1k + 
                                   (est_output / 1000) * pricing.output_cost_per_1k)
                        
                        predictions["cost_comparisons"][model] = {
                            "estimated_monthly_cost": est_cost,
                            "cost_per_1k_tokens": ((est_cost / total_tokens) * 1000) if total_tokens > 0 else 0
                        }
            
            # Generate recommendations
            predictions["recommendations"] = self._generate_recommendations(summary_30d, predictions)
            
            return predictions
    
    def _estimate_paid_cost(self, free_model: str, tokens: int) -> float:
        """Estimate cost if using equivalent paid model"""
        # Map free models to their paid equivalents
        paid_equivalents = {
            "qwen/qwen3-coder:free": "qwen/qwen3-coder",
            "deepseek/deepseek-r1-0528:free": "deepseek/deepseek-r1-0528",
            "google/gemini-flash-1.5:free": "google/gemini-pro-1.5"
        }
        
        paid_model = paid_equivalents.get(free_model)
        if paid_model and paid_model in self.MODEL_PRICING:
            pricing = self.MODEL_PRICING[paid_model]
            # Estimate 60/40 input/output split
            est_input = int(tokens * 0.6)
            est_output = int(tokens * 0.4)
            return ((est_input / 1000) * pricing.input_cost_per_1k + 
                   (est_output / 1000) * pricing.output_cost_per_1k)
        
        return 0.0
    
    def _generate_recommendations(self, summary: CostSummary, predictions: Dict) -> List[str]:
        """Generate cost optimization recommendations"""
        recommendations = []
        
        # Check free tier usage
        for model, status in predictions["free_tier_status"].items():
            if status["usage_percent"] > 80:
                recommendations.append(
                    f"[WARNING] {model} is at {status['usage_percent']:.1f}% of free tier limit. "
                    f"Consider switching to a paid alternative or monitoring usage."
                )
            elif status["usage_percent"] > 50:
                recommendations.append(
                    f"[METRICS] {model} is at {status['usage_percent']:.1f}% of free tier limit. "
                    f"Monitor usage to avoid hitting limits."
                )
        
        # Cost optimization suggestions
        if summary.total_cost > 50:  # If spending more than $50/month
            cheapest_models = sorted(
                predictions["cost_comparisons"].items(),
                key=lambda x: x[1]["cost_per_1k_tokens"]
            )[:3]
            
            if cheapest_models:
                recommendations.append(
                    f"[EMOJI] Consider switching to more cost-effective models: "
                    f"{', '.join([model for model, _ in cheapest_models])}"
                )
        
        # Local model suggestion
        if "local-model" not in summary.by_model and summary.total_cost > 20:
            recommendations.append(
                "[LOCAL] Consider using LM Studio for local inference to reduce API costs. "
                "Current spending could justify local GPU investment."
            )
        
        # Efficiency recommendations
        avg_tokens_per_request = summary.total_tokens / summary.total_requests if summary.total_requests > 0 else 0
        if avg_tokens_per_request > 2000:
            recommendations.append(
                "[EMOJI] Consider optimizing prompts to reduce token usage. "
                f"Average {avg_tokens_per_request:.0f} tokens per request."
            )
        
        return recommendations
    
    def export_cost_report(self, days: int = 30, format: str = "json") -> str:
        """
        Export detailed cost report
        
        Args:
            days: Number of days to include
            format: "json" or "csv"
        """
        summary = self.get_usage_summary(days)
        predictions = self.get_cost_predictions()
        
        report_data = {
            "report_date": datetime.now().isoformat(),
            "period_days": days,
            "summary": asdict(summary),
            "predictions": predictions,
            "model_pricing": {k: asdict(v) for k, v in self.MODEL_PRICING.items()}
        }
        
        if format.lower() == "json":
            return json.dumps(report_data, indent=2, default=str)
        elif format.lower() == "csv":
            # Generate CSV format
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write summary
            writer.writerow(["Summary"])
            writer.writerow(["Total Cost", f"${summary.total_cost:.4f}"])
            writer.writerow(["Total Tokens", summary.total_tokens])
            writer.writerow(["Total Requests", summary.total_requests])
            writer.writerow(["Projected Monthly", f"${summary.projected_monthly:.2f}"])
            writer.writerow([])
            
            # Write by model
            writer.writerow(["Model", "Cost", "Usage"])
            for model, cost in summary.by_model.items():
                usage = summary.free_tier_usage.get(model, "N/A")
                writer.writerow([model, f"${cost:.4f}", usage])
            
            return output.getvalue()
        
        return json.dumps(report_data, indent=2, default=str)
    
    def set_budget_alert(self, monthly_budget: float, alert_threshold: float = 0.8):
        """
        Set budget alert threshold
        
        Args:
            monthly_budget: Monthly budget in USD
            alert_threshold: Alert when reaching this percentage (0.0-1.0)
        """
        # Store budget settings
        settings = {
            "monthly_budget": monthly_budget,
            "alert_threshold": alert_threshold,
            "set_date": datetime.now().isoformat()
        }
        
        with open("budget_settings.json", "w") as f:
            json.dump(settings, f, indent=2)
    
    def check_budget_status(self) -> Dict[str, Any]:
        """Check current budget status against set budget"""
        try:
            with open("budget_settings.json", "r") as f:
                settings = json.load(f)
        except FileNotFoundError:
            return {"status": "no_budget_set"}
        
        # Get current month spending
        now = datetime.now()
        start_of_month = datetime(now.year, now.month, 1)
        days_in_month = (now - start_of_month).days + 1
        
        summary = self.get_usage_summary(days=days_in_month)
        
        budget = settings["monthly_budget"]
        threshold = settings["alert_threshold"]
        usage_percent = (summary.total_cost / budget) if budget > 0 else 0
        
        status = {
            "monthly_budget": budget,
            "current_spending": summary.total_cost,
            "usage_percent": usage_percent * 100,
            "alert_threshold": threshold * 100,
            "projected_monthly": summary.projected_monthly,
            "over_budget": summary.projected_monthly > budget,
            "needs_alert": usage_percent >= threshold
        }
        
        return status

# Global instance
cost_tracker = CostTracker()