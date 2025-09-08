"""
Action and Reasoning Logger for DuckBot v3.0.7
Comprehensive logging system that captures all AI decisions, actions, and reasoning
"""

import json
import time
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

class ActionReasoningLogger:
    """
    Enterprise-grade action and reasoning logger that tracks:
    - AI model routing decisions and fallbacks
    - Rate limiting triggers and responses  
    - Server management actions
    - User interaction patterns
    - System performance decisions
    - Error handling and recovery actions
    """
    
    def __init__(self, db_path: str = "logs/action_reasoning.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._lock = threading.Lock()
        self._init_database()
        
        # Setup file logging for action/reasoning events
        self.logger = logging.getLogger("ActionReasoningLogger")
        self.logger.setLevel(logging.INFO)
        
        # Create file handler for action logs
        log_file = self.db_path.parent / "action_reasoning.log"
        handler = logging.FileHandler(log_file, encoding='utf-8')
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def _init_database(self):
        """Initialize SQLite database for action/reasoning storage"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS action_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    action_type TEXT NOT NULL,
                    component TEXT NOT NULL,
                    action_description TEXT NOT NULL,
                    reasoning TEXT NOT NULL,
                    context_data TEXT,
                    outcome TEXT,
                    execution_time_ms INTEGER,
                    user_id TEXT,
                    session_id TEXT,
                    severity TEXT DEFAULT 'INFO'
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_action_timestamp 
                ON action_logs(timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_action_type_component 
                ON action_logs(action_type, component)
            """)
    
    def log_action(self, 
                   action_type: str,
                   component: str, 
                   action_description: str,
                   reasoning: str,
                   context_data: Optional[Dict[str, Any]] = None,
                   outcome: Optional[str] = None,
                   execution_time_ms: Optional[int] = None,
                   user_id: Optional[str] = None,
                   session_id: Optional[str] = None,
                   severity: str = "INFO"):
        """
        Log an action with its reasoning
        
        Args:
            action_type: Type of action (AI_ROUTING, FALLBACK, RATE_LIMITING, SERVER_MGMT, etc.)
            component: Component performing action (ai_router_gpt, webui, server_manager, etc.)
            action_description: What action was taken
            reasoning: Why this action was taken
            context_data: Additional context information
            outcome: Result of the action
            execution_time_ms: How long the action took
            user_id: User who triggered the action
            session_id: Session identifier
            severity: Log severity (INFO, WARNING, ERROR, CRITICAL)
        """
        
        timestamp = datetime.now()
        context_json = json.dumps(context_data) if context_data else None
        
        # Log to file
        log_message = f"[{action_type}] {component}: {action_description} | Reasoning: {reasoning}"
        if outcome:
            log_message += f" | Outcome: {outcome}"
        
        if severity == "ERROR":
            self.logger.error(log_message)
        elif severity == "WARNING":
            self.logger.warning(log_message)
        elif severity == "CRITICAL":
            self.logger.critical(log_message)
        else:
            self.logger.info(log_message)
        
        # Store in database
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT INTO action_logs 
                        (timestamp, action_type, component, action_description, reasoning, 
                         context_data, outcome, execution_time_ms, user_id, session_id, severity)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (timestamp, action_type, component, action_description, reasoning,
                          context_json, outcome, execution_time_ms, user_id, session_id, severity))
            except Exception as e:
                self.logger.error(f"Failed to store action log in database: {e}")
    
    def log_ai_routing_decision(self, 
                               prompt: str,
                               chosen_model: str, 
                               reasoning: str,
                               available_models: List[str],
                               rate_limit_status: Dict[str, Any],
                               execution_time_ms: int,
                               outcome: str,
                               user_id: str = None,
                               bucket_type: Optional[str] = None):
        """Log AI model routing decisions"""
        # Prepare safe prompt fields (cap full prompt to keep logs manageable)
        safe_prompt = prompt or ""
        prompt_preview = safe_prompt[:100] + "..." if len(safe_prompt) > 100 else safe_prompt
        safe_prompt_full = safe_prompt[:2000]

        context = {
            "prompt_length": len(safe_prompt),
            "prompt_preview": prompt_preview,
            "prompt": safe_prompt_full,
            "available_models": available_models,
            "rate_limit_status": rate_limit_status,
            "chosen_model": chosen_model
        }
        if bucket_type:
            context["bucket_type"] = bucket_type
        
        self.log_action(
            action_type="AI_ROUTING",
            component="ai_router_gpt",
            action_description=f"Routed request to {chosen_model}",
            reasoning=reasoning,
            context_data=context,
            outcome=outcome,
            execution_time_ms=execution_time_ms,
            user_id=user_id
        )
    
    def log_fallback_decision(self,
                             original_model: str,
                             fallback_model: str,
                             error_type: str,
                             reasoning: str,
                             attempt_number: int,
                             user_id: str = None):
        """Log model fallback decisions"""
        context = {
            "original_model": original_model,
            "fallback_model": fallback_model,
            "error_type": error_type,
            "attempt_number": attempt_number
        }
        
        severity = "WARNING" if attempt_number == 1 else "ERROR"
        
        self.log_action(
            action_type="FALLBACK",
            component="ai_router_gpt", 
            action_description=f"Fallback from {original_model} to {fallback_model}",
            reasoning=reasoning,
            context_data=context,
            outcome=f"Attempt {attempt_number}",
            user_id=user_id,
            severity=severity
        )
    
    def log_rate_limiting_action(self,
                                bucket_type: str,
                                action_taken: str,
                                reasoning: str,
                                bucket_status: Dict[str, Any],
                                user_id: str = None):
        """Log rate limiting decisions and actions"""
        context = {
            "bucket_type": bucket_type,
            "bucket_status": bucket_status,
            "tokens_available": bucket_status.get("tokens", 0),
            "last_refill": bucket_status.get("last_refill", "unknown")
        }
        
        severity = "WARNING" if "blocked" in action_taken.lower() else "INFO"
        
        self.log_action(
            action_type="RATE_LIMITING",
            component="ai_router_gpt",
            action_description=action_taken,
            reasoning=reasoning,
            context_data=context,
            user_id=user_id,
            severity=severity
        )
    
    def log_server_management_action(self,
                                   server_name: str,
                                   action: str,
                                   reasoning: str,
                                   outcome: str,
                                   execution_time_ms: int = None):
        """Log server management decisions"""
        context = {
            "server_name": server_name,
            "action": action
        }
        
        severity = "ERROR" if "failed" in outcome.lower() else "INFO"
        
        self.log_action(
            action_type="SERVER_MGMT",
            component="server_manager",
            action_description=f"{action} {server_name}",
            reasoning=reasoning,
            context_data=context,
            outcome=outcome,
            execution_time_ms=execution_time_ms,
            severity=severity
        )
    
    def get_recent_actions(self, 
                          hours: int = 24, 
                          action_type: Optional[str] = None,
                          component: Optional[str] = None,
                          limit: int = 1000) -> List[Dict[str, Any]]:
        """Retrieve recent actions with optional filtering"""
        
        query = """
            SELECT * FROM action_logs 
            WHERE timestamp >= datetime('now', '-{} hours')
        """.format(hours)
        
        params = []
        
        if action_type:
            query += " AND action_type = ?"
            params.append(action_type)
            
        if component:
            query += " AND component = ?"
            params.append(component)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            
            results = []
            for row in cursor.fetchall():
                row_dict = dict(row)
                # Parse context_data JSON
                if row_dict['context_data']:
                    try:
                        row_dict['context_data'] = json.loads(row_dict['context_data'])
                    except json.JSONDecodeError:
                        row_dict['context_data'] = {}
                
                results.append(row_dict)
            
            return results
    
    def get_action_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary statistics for actions in the specified time period"""
        
        with sqlite3.connect(self.db_path) as conn:
            # Total actions by type
            cursor = conn.execute("""
                SELECT action_type, COUNT(*) as count
                FROM action_logs 
                WHERE timestamp >= datetime('now', '-{} hours')
                GROUP BY action_type
                ORDER BY count DESC
            """.format(hours))
            
            actions_by_type = dict(cursor.fetchall())
            
            # Actions by severity
            cursor = conn.execute("""
                SELECT severity, COUNT(*) as count
                FROM action_logs 
                WHERE timestamp >= datetime('now', '-{} hours')
                GROUP BY severity
            """.format(hours))
            
            actions_by_severity = dict(cursor.fetchall())
            
            # Recent errors
            cursor = conn.execute("""
                SELECT action_type, component, action_description, reasoning, timestamp
                FROM action_logs 
                WHERE timestamp >= datetime('now', '-{} hours')
                  AND severity IN ('ERROR', 'CRITICAL')
                ORDER BY timestamp DESC
                LIMIT 10
            """.format(hours))
            
            recent_errors = []
            for row in cursor.fetchall():
                recent_errors.append({
                    "action_type": row[0],
                    "component": row[1], 
                    "action_description": row[2],
                    "reasoning": row[3],
                    "timestamp": row[4]
                })
            
            return {
                "time_period_hours": hours,
                "total_actions": sum(actions_by_type.values()),
                "actions_by_type": actions_by_type,
                "actions_by_severity": actions_by_severity,
                "recent_errors": recent_errors,
                "generated_at": datetime.now().isoformat()
            }
    
    def cleanup_old_logs(self, days: int = 30):
        """Remove action logs older than specified days"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                DELETE FROM action_logs 
                WHERE timestamp < datetime('now', '-{} days')
            """.format(days))
            
            deleted_count = cursor.rowcount
            self.logger.info(f"Cleaned up {deleted_count} action logs older than {days} days")
            return deleted_count


# Global instance
action_logger = ActionReasoningLogger()
