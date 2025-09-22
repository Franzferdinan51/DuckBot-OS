#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Error handling and logging framework for the modular launcher
"""

import logging
import traceback
import sys
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import json

class ErrorLevel(Enum):
    """Error severity levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error categories"""
    ENVIRONMENT = "environment"
    CONFIGURATION = "configuration"
    SERVICE = "service"
    PORT = "port"
    NETWORK = "network"
    SYSTEM = "system"
    USER_INPUT = "user_input"
    UNKNOWN = "unknown"

@dataclass
class ErrorInfo:
    """Error information structure"""
    timestamp: float
    level: ErrorLevel
    category: ErrorCategory
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolution_notes: Optional[str] = None

class ErrorHandler:
    """Centralized error handling and logging"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.project_root = Path(__file__).parent.parent.parent
        self.log_dir = self.project_root / "logs"
        self.error_log_file = self.log_dir / "launcher_errors.log"
        self.error_history: List[ErrorInfo] = []
        self.error_callbacks: Dict[ErrorCategory, List[Callable]] = {}
        self.max_error_history = 1000
        self.auto_recovery_enabled = True

        # Setup error logging
        self._setup_error_logging()

    def _setup_error_logging(self):
        """Setup dedicated error logging"""
        self.log_dir.mkdir(exist_ok=True)

        # Create error file handler
        error_handler = logging.FileHandler(
            self.error_log_file,
            encoding='utf-8',
            mode='a'  # Append mode
        )
        error_handler.setLevel(logging.DEBUG)

        # Error formatter
        error_formatter = logging.Formatter(
            '%(asctime)s - [%(levelname)s] - %(message)s'
        )
        error_handler.setFormatter(error_formatter)

        # Add to logger
        self.logger.addHandler(error_handler)

    def handle_error(self,
                    level: ErrorLevel,
                    category: ErrorCategory,
                    message: str,
                    details: Dict[str, Any] = None,
                    context: Dict[str, Any] = None,
                    stack_trace: str = None) -> ErrorInfo:
        """Handle an error with comprehensive logging"""
        if details is None:
            details = {}
        if context is None:
            context = {}

        # Create error info
        error_info = ErrorInfo(
            timestamp=time.time(),
            level=level,
            category=category,
            message=message,
            details=details,
            stack_trace=stack_trace or traceback.format_stack()[-3:-1],
            context=context
        )

        # Add to history
        self.error_history.append(error_info)
        if len(self.error_history) > self.max_error_history:
            self.error_history = self.error_history[-self.max_error_history:]

        # Log the error
        self._log_error(error_info)

        # Trigger callbacks
        self._trigger_callbacks(error_info)

        # Attempt auto-recovery for critical errors
        if self.auto_recovery_enabled and level in [ErrorLevel.ERROR, ErrorLevel.CRITICAL]:
            self._attempt_auto_recovery(error_info)

        return error_info

    def _log_error(self, error_info: ErrorInfo):
        """Log error information"""
        log_message = f"[{error_info.category.value.upper()}] {error_info.message}"

        # Map error levels to logging levels
        log_levels = {
            ErrorLevel.DEBUG: logging.DEBUG,
            ErrorLevel.INFO: logging.INFO,
            ErrorLevel.WARNING: logging.WARNING,
            ErrorLevel.ERROR: logging.ERROR,
            ErrorLevel.CRITICAL: logging.CRITICAL
        }

        log_level = log_levels.get(error_info.level, logging.ERROR)

        # Create a temporary logger for error-specific formatting
        error_logger = logging.getLogger(f"{self.logger.name}.errors")
        if not error_logger.handlers:
            # Add a file handler specifically for errors
            error_file_handler = logging.FileHandler(
                self.error_log_file,
                encoding='utf-8',
                mode='a'
            )
            error_file_handler.setLevel(logging.DEBUG)

            # Simple formatter without extra fields
            simple_formatter = logging.Formatter(
                '%(asctime)s - [%(levelname)s] - %(message)s'
            )
            error_file_handler.setFormatter(simple_formatter)
            error_logger.addHandler(error_file_handler)
            error_logger.propagate = False

        # Log the error with context information in the message
        context_str = json.dumps(error_info.context, default=str)
        full_message = f"{log_message}\nContext: {context_str}"
        if error_info.stack_trace:
            full_message += f"\nStack Trace: {error_info.stack_trace}"

        error_logger.log(log_level, full_message)

        # Also log to main logger without extra fields
        self.logger.log(log_level, log_message)

    def _trigger_callbacks(self, error_info: ErrorInfo):
        """Trigger registered error callbacks"""
        if error_info.category in self.error_callbacks:
            for callback in self.error_callbacks[error_info.category]:
                try:
                    callback(error_info)
                except Exception as e:
                    self.logger.error(f"Error callback failed: {e}")

    def _attempt_auto_recovery(self, error_info: ErrorInfo):
        """Attempt automatic recovery for certain error types"""
        recovery_actions = {
            ErrorCategory.PORT: self._recover_port_error,
            ErrorCategory.SERVICE: self._recover_service_error,
            ErrorCategory.ENVIRONMENT: self._recover_environment_error,
            ErrorCategory.CONFIGURATION: self._recover_config_error
        }

        if error_info.category in recovery_actions:
            try:
                recovery_success = recovery_actions[error_info.category](error_info)
                if recovery_success:
                    error_info.resolved = True
                    error_info.resolution_notes = "Auto-recovery successful"
                    self.logger.info(f"Auto-recovery successful for: {error_info.message}")
            except Exception as e:
                self.logger.error(f"Auto-recovery failed: {e}")

    def _recover_port_error(self, error_info: ErrorInfo) -> bool:
        """Attempt to recover from port-related errors"""
        # Implementation would coordinate with PortManager
        self.logger.info("Attempting port error recovery...")
        # Placeholder for port recovery logic
        return False

    def _recover_service_error(self, error_info: ErrorInfo) -> bool:
        """Attempt to recover from service-related errors"""
        # Implementation would coordinate with ServiceManager
        self.logger.info("Attempting service error recovery...")
        # Placeholder for service recovery logic
        return False

    def _recover_environment_error(self, error_info: ErrorInfo) -> bool:
        """Attempt to recover from environment-related errors"""
        self.logger.info("Attempting environment error recovery...")

        # Try to fix common environment issues
        if "Python" in error_info.message:
            return self._fix_python_environment()
        elif "PATH" in error_info.message:
            return self._fix_path_environment()

        return False

    def _recover_config_error(self, error_info: ErrorInfo) -> bool:
        """Attempt to recover from configuration-related errors"""
        self.logger.info("Attempting configuration error recovery...")

        # Try to reload configurations
        # Implementation would coordinate with ConfigManager
        return False

    def _fix_python_environment(self) -> bool:
        """Attempt to fix Python environment issues"""
        try:
            # Check if we can find a working Python
            python_candidates = ["python", "python3", "py", "py -3"]
            for candidate in python_candidates:
                result = os.system(f"{candidate} --version >nul 2>&1")
                if result == 0:
                    os.environ["PYTHON_CMD"] = candidate
                    return True
        except Exception:
            pass
        return False

    def _fix_path_environment(self) -> bool:
        """Attempt to fix PATH environment issues"""
        try:
            # Add common Python paths
            common_paths = [
                r"C:\Python39",
                r"C:\Python310",
                r"C:\Python311",
                r"C:\Python312",
                r"C:\Program Files\Python39",
                r"C:\Program Files\Python310",
                r"C:\Program Files\Python311",
                r"C:\Program Files\Python312"
            ]

            current_path = os.environ.get("PATH", "")
            for path in common_paths:
                if os.path.exists(path) and path not in current_path:
                    os.environ["PATH"] = f"{path};{current_path}"
                    return True

        except Exception:
            pass
        return False

    def register_callback(self, category: ErrorCategory, callback: Callable):
        """Register a callback for specific error categories"""
        if category not in self.error_callbacks:
            self.error_callbacks[category] = []
        self.error_callbacks[category].append(callback)

    def get_error_history(self,
                         category: Optional[ErrorCategory] = None,
                         level: Optional[ErrorLevel] = None,
                         limit: int = 100) -> List[ErrorInfo]:
        """Get error history with optional filtering"""
        filtered_errors = self.error_history

        if category:
            filtered_errors = [e for e in filtered_errors if e.category == category]

        if level:
            filtered_errors = [e for e in filtered_errors if e.level == level]

        return filtered_errors[-limit:]

    def get_error_summary(self) -> Dict[str, Any]:
        """Get error summary statistics"""
        if not self.error_history:
            return {"total_errors": 0}

        total_errors = len(self.error_history)
        errors_by_category = {}
        errors_by_level = {}
        resolved_count = sum(1 for e in self.error_history if e.resolved)

        for error in self.error_history:
            # Count by category
            cat_name = error.category.value
            errors_by_category[cat_name] = errors_by_category.get(cat_name, 0) + 1

            # Count by level
            level_name = error.level.value
            errors_by_level[level_name] = errors_by_level.get(level_name, 0) + 1

        return {
            "total_errors": total_errors,
            "resolved_errors": resolved_count,
            "unresolved_errors": total_errors - resolved_count,
            "errors_by_category": errors_by_category,
            "errors_by_level": errors_by_level,
            "resolution_rate": (resolved_count / total_errors * 100) if total_errors > 0 else 0
        }

    def clear_error_history(self):
        """Clear error history"""
        self.error_history.clear()
        self.logger.info("Error history cleared")

    def export_errors(self, file_path: str) -> bool:
        """Export error history to file"""
        try:
            export_data = {
                "export_timestamp": time.time(),
                "total_errors": len(self.error_history),
                "errors": [
                    {
                        "timestamp": error.timestamp,
                        "level": error.level.value,
                        "category": error.category.value,
                        "message": error.message,
                        "details": error.details,
                        "stack_trace": error.stack_trace,
                        "context": error.context,
                        "resolved": error.resolved,
                        "resolution_notes": error.resolution_notes
                    }
                    for error in self.error_history
                ]
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)

            self.logger.info(f"Error history exported to: {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to export error history: {e}")
            return False

    def create_error_report(self) -> str:
        """Create a human-readable error report"""
        if not self.error_history:
            return "No errors to report."

        summary = self.get_error_summary()
        recent_errors = self.get_error_history(limit=10)

        report = f"""
DuckBot Launcher Error Report
Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}
================================

SUMMARY:
- Total Errors: {summary['total_errors']}
- Resolved: {summary['resolved_errors']}
- Unresolved: {summary['unresolved_errors']}
- Resolution Rate: {summary['resolution_rate']:.1f}%

ERRORS BY CATEGORY:
"""

        for category, count in summary['errors_by_category'].items():
            report += f"- {category.upper()}: {count}\n"

        report += "\nERRORS BY SEVERITY:\n"
        for level, count in summary['errors_by_level'].items():
            report += f"- {level.upper()}: {count}\n"

        report += "\nRECENT ERRORS:\n"
        for i, error in enumerate(recent_errors[-5:], 1):
            report += f"""
{i}. [{error.level.value.upper()}] {error.message}
   Category: {error.category.value}
   Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(error.timestamp))}
   Resolved: {'Yes' if error.resolved else 'No'}
"""

        return report

    def wrap_function(self, func, error_category: ErrorCategory = ErrorCategory.UNKNOWN):
        """Decorator to wrap functions with error handling"""
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                self.handle_error(
                    level=ErrorLevel.ERROR,
                    category=error_category,
                    message=f"Function {func.__name__} failed: {str(e)}",
                    details={"function": func.__name__, "args": str(args), "kwargs": str(kwargs)}
                )
                raise  # Re-raise the exception
        return wrapper

    # Simplified error handling method for easier usage
    def handle_simple_error(self, error_or_message, category=None, details=None):
        """Simple error handling method for basic usage"""
        if isinstance(error_or_message, Exception):
            # If first parameter is an exception, extract info
            error = error_or_message
            level = ErrorLevel.ERROR
            category = category or ErrorCategory.UNKNOWN
            message = str(error)
            details = details or {"exception_type": type(error).__name__}
        else:
            # Use provided parameters
            level = ErrorLevel.ERROR
            category = category or ErrorCategory.UNKNOWN
            message = error_or_message

        return self.handle_error(
            level=level,
            category=category,
            message=message,
            details=details or {},
            context={},
            stack_trace=None
        )