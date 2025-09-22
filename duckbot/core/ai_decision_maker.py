#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DuckBot AI Decision Making System
Enhanced AI decision making with system state awareness and autonomous capabilities
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import statistics
import uuid
from pathlib import Path

# Local imports
from duckbot.core.ai_system_controller import get_ai_controller, get_system_status_for_ai
from duckbot.core.monitoring_system import get_monitoring
from duckbot.core.health_predictive_maintenance import PredictiveMaintenanceSystem
from duckbot.agents.intelligent_agents import agent_orchestrator, AgentType, AgentContext

logger = logging.getLogger(__name__)

class DecisionCategory(Enum):
    SYSTEM_OPTIMIZATION = "system_optimization"
    ERROR_RECOVERY = "error_recovery"
    PERFORMANCE_TUNING = "performance_tuning"
    RESOURCE_MANAGEMENT = "resource_management"
    SERVICE_MANAGEMENT = "service_management"
    PREDICTIVE_ACTION = "predictive_action"
    AGENT_COORDINATION = "agent_coordination"
    COST_OPTIMIZATION = "cost_optimization"
    SECURITY_RESPONSE = "security_response"

class DecisionConfidence(Enum):
    VERY_LOW = 0.1
    LOW = 0.3
    MEDIUM = 0.5
    HIGH = 0.7
    VERY_HIGH = 0.9

class DecisionPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class DecisionFactor:
    """Factor influencing AI decision making"""
    name: str
    weight: float
    value: float
    normalized_value: float
    category: str
    description: str

@dataclass
class AIDecision:
    """AI decision with confidence and reasoning"""
    id: str
    category: DecisionCategory
    action: str
    confidence: float
    priority: DecisionPriority
    reasoning: List[str]
    factors: List[DecisionFactor]
    expected_outcome: Dict[str, Any]
    risks: List[str]
    alternatives: List[str]
    timestamp: datetime
    execution_plan: Dict[str, Any]
    auto_execute: bool
    requires_approval: bool

@dataclass
class DecisionContext:
    """Context for AI decision making"""
    system_state: Dict[str, Any]
    historical_data: Dict[str, Any]
    user_preferences: Dict[str, Any]
    business_rules: Dict[str, Any]
    time_constraints: Dict[str, Any]
    resource_constraints: Dict[str, Any]

@dataclass
class DecisionOutcome:
    """Result of executed decision"""
    decision_id: str
    success: bool
    actual_outcome: Dict[str, Any]
    execution_time_ms: float
    deviation_from_expected: float
    lessons_learned: List[str]
    timestamp: datetime

class AIDecisionMaker:
    """Advanced AI decision making system for autonomous system management"""

    def __init__(self):
        self.ai_controller = get_ai_controller()
        self.monitoring = get_monitoring()
        self.maintenance_system = PredictiveMaintenanceSystem()

        # Decision history and learning
        self.decision_history: List[AIDecision] = []
        self.decision_outcomes: List[DecisionOutcome] = []
        self.decision_patterns: Dict[str, Any] = {}

        # Decision making configuration
        self.decision_thresholds = {
            "auto_execute": 0.8,
            "high_confidence": 0.7,
            "medium_confidence": 0.5,
            "risk_tolerance": 0.6
        }

        # Learning weights (adapted over time)
        self.learning_weights = {
            "historical_success": 0.3,
            "system_state": 0.25,
            "resource_availability": 0.2,
            "time_criticality": 0.15,
            "user_preference": 0.1
        }

        # Performance tracking
        self.performance_metrics = {
            "total_decisions": 0,
            "successful_decisions": 0,
            "auto_executed": 0,
            "avg_confidence": 0.0,
            "avg_accuracy": 0.0,
            "prevented_issues": 0
        }

        # Business rules and constraints
        self.business_rules = self._load_business_rules()
        self.resource_constraints = self._load_resource_constraints()

        logger.info("AI Decision Maker initialized")

    def _load_business_rules(self) -> Dict[str, Any]:
        """Load business rules for decision making"""
        return {
            "maintenance_window": {"start": "02:00", "end": "04:00", "timezone": "UTC"},
            "max_downtime": {"critical_services": "5m", "normal_services": "30m"},
            "cost_thresholds": {"monthly_limit": 1000, "alert_threshold": 800},
            "performance_sla": {"response_time": "2s", "uptime": "99.9%"},
            "security_rules": {
                "auto_restart": True,
                "isolate_compromised": True,
                "alert_threshold": "medium"
            }
        }

    def _load_resource_constraints(self) -> Dict[str, Any]:
        """Load resource constraints for decision making"""
        return {
            "max_cpu_usage": 85.0,
            "max_memory_usage": 85.0,
            "max_disk_usage": 90.0,
            "min_free_vram": 1.0,  # GB
            "max_concurrent_operations": 5,
            "backup_requirements": {
                "critical_data": "daily",
                "user_data": "weekly",
                "system_config": "monthly"
            }
        }

    async def make_decision(self, category: DecisionCategory, context: DecisionContext) -> AIDecision:
        """Make an AI decision based on context and analysis"""
        start_time = time.time()

        try:
            # Analyze decision context
            analysis_result = await self._analyze_decision_context(category, context)

            # Generate decision factors
            factors = self._generate_decision_factors(category, context, analysis_result)

            # Calculate decision confidence
            confidence = self._calculate_decision_confidence(factors, category)

            # Generate decision alternatives
            alternatives = self._generate_decision_alternatives(category, context, factors)

            # Select best action
            action, reasoning = self._select_best_action(category, factors, alternatives)

            # Determine priority and auto-execution
            priority = self._determine_priority(category, confidence, context)
            auto_execute, requires_approval = self._determine_execution_permissions(
                category, confidence, priority, context
            )

            # Create execution plan
            execution_plan = self._create_execution_plan(action, category, context)

            # Estimate outcome
            expected_outcome = self._estimate_expected_outcome(action, category, factors)

            # Identify risks
            risks = self._identify_risks(action, category, context, factors)

            # Create decision object
            decision = AIDecision(
                id=str(uuid.uuid4()),
                category=category,
                action=action,
                confidence=confidence,
                priority=priority,
                reasoning=reasoning,
                factors=factors,
                expected_outcome=expected_outcome,
                risks=risks,
                alternatives=alternatives,
                timestamp=datetime.now(),
                execution_plan=execution_plan,
                auto_execute=auto_execute,
                requires_approval=requires_approval
            )

            # Record decision
            self._record_decision(decision)

            # Update performance metrics
            self._update_decision_metrics(decision)

            logger.info(f"AI Decision made: {category.value} - {action} (confidence: {confidence:.2f})")

            return decision

        except Exception as e:
            logger.error(f"Error making decision: {e}")
            # Return a safe fallback decision
            return AIDecision(
                id=str(uuid.uuid4()),
                category=category,
                action="no_action",
                confidence=0.1,
                priority=DecisionPriority.LOW,
                reasoning=["Error in decision making process"],
                factors=[],
                expected_outcome={},
                risks=["No action taken due to error"],
                alternatives=[],
                timestamp=datetime.now(),
                execution_plan={},
                auto_execute=False,
                requires_approval=True
            )

    async def _analyze_decision_context(self, category: DecisionCategory, context: DecisionContext) -> Dict[str, Any]:
        """Analyze the decision context comprehensively"""
        analysis = {
            "system_health": self._analyze_system_health(context),
            "resource_availability": self._analyze_resource_availability(context),
            "time_constraints": self._analyze_time_constraints(context),
            "historical_patterns": self._analyze_historical_patterns(category, context),
            "business_rule_compliance": self._analyze_business_rules(category, context),
            "risk_assessment": self._assess_risks(category, context)
        }

        return analysis

    def _analyze_system_health(self, context: DecisionContext) -> Dict[str, Any]:
        """Analyze current system health"""
        system_state = context.system_state

        # Calculate system health score
        health_score = system_state.get("ai_control_status", {}).get("system_health_score", 0.5)

        # Identify unhealthy components
        unhealthy_services = [
            name for name, info in system_state.get("service_status", {}).items()
            if info.get("status") == "unhealthy"
        ]

        # Check resource usage
        resource_usage = system_state.get("resource_usage", {})
        high_usage_resources = []
        for resource, usage in resource_usage.items():
            if isinstance(usage, (int, float)) and usage > 85:
                high_usage_resources.append(resource)

        return {
            "health_score": health_score,
            "unhealthy_services": unhealthy_services,
            "high_usage_resources": high_usage_resources,
            "active_alerts": len(system_state.get("active_alerts", [])),
            "overall_status": "healthy" if health_score > 0.8 else "degraded" if health_score > 0.5 else "unhealthy"
        }

    def _analyze_resource_availability(self, context: DecisionContext) -> Dict[str, Any]:
        """Analyze resource availability and constraints"""
        system_state = context.system_state
        constraints = self.resource_constraints

        resource_usage = system_state.get("resource_usage", {})

        availability = {}
        for resource, current_usage in resource_usage.items():
            if isinstance(current_usage, (int, float)):
                max_usage = constraints.get(f"max_{resource}_usage", 100.0)
                available = max(0, max_usage - current_usage)
                availability[resource] = {
                    "current_usage": current_usage,
                    "max_usage": max_usage,
                    "available": available,
                    "utilization_percent": (current_usage / max_usage) * 100
                }

        return {
            "resource_availability": availability,
            "constrained_resources": [
                resource for resource, data in availability.items()
                if data["available"] <= 10
            ],
            "overall_capacity": "high" if all(data["available"] > 20 for data in availability.values()) else "medium"
        }

    def _analyze_time_constraints(self, context: DecisionContext) -> Dict[str, Any]:
        """Analyze time constraints and windows"""
        current_time = datetime.now()
        time_constraints = context.time_constraints

        # Check if in maintenance window
        maintenance_window = self.business_rules["maintenance_window"]
        in_maintenance_window = self._is_time_in_window(
            current_time.time(),
            maintenance_window["start"],
            maintenance_window["end"]
        )

        # Check for business hours (assuming 9-5 weekdays)
        is_business_hours = (
            current_time.weekday() < 5 and
            9 <= current_time.hour < 17
        )

        return {
            "current_time": current_time.isoformat(),
            "in_maintenance_window": in_maintenance_window,
            "is_business_hours": is_business_hours,
            "time_sensitivity": time_constraints.get("sensitivity", "normal"),
            "deadline": time_constraints.get("deadline"),
            "optimal_execution_time": self._determine_optimal_execution_time(
                context, is_business_hours, in_maintenance_window
            )
        }

    def _is_time_in_window(self, current_time, window_start, window_end) -> bool:
        """Check if current time is within time window"""
        from datetime import datetime as dt

        start = dt.strptime(window_start, "%H:%M").time()
        end = dt.strptime(window_end, "%H:%M").time()

        return start <= current_time <= end

    def _determine_optimal_execution_time(self, context: DecisionContext, is_business_hours: bool,
                                       in_maintenance_window: bool) -> str:
        """Determine optimal execution time based on context"""
        time_sensitivity = context.time_constraints.get("sensitivity", "normal")

        if time_sensitivity == "critical":
            return "immediate"
        elif in_maintenance_window:
            return "maintenance_window"
        elif not is_business_hours:
            return "off_hours"
        else:
            return "scheduled"

    def _analyze_historical_patterns(self, category: DecisionCategory, context: DecisionContext) -> Dict[str, Any]:
        """Analyze historical patterns and outcomes"""
        historical_data = context.historical_data

        # Get similar past decisions
        similar_decisions = [
            decision for decision in self.decision_history
            if decision.category == category
        ]

        if not similar_decisions:
            return {"sufficient_data": False, "recommendation": "insufficient_data"}

        # Analyze success patterns
        successful_decisions = [
            decision for decision in similar_decisions
            if self._get_decision_outcome(decision.id, {}).get("success", False)
        ]

        success_rate = len(successful_decisions) / len(similar_decisions)

        # Identify common successful actions
        successful_actions = {}
        for decision in successful_decisions:
            action = decision.action
            successful_actions[action] = successful_actions.get(action, 0) + 1

        most_successful_action = max(successful_actions.items(), key=lambda x: x[1])[0] if successful_actions else None

        return {
            "sufficient_data": True,
            "success_rate": success_rate,
            "total_similar_decisions": len(similar_decisions),
            "most_successful_action": most_successful_action,
            "confidence_in_patterns": min(0.9, success_rate + (len(similar_decisions) / 100))
        }

    def _get_decision_outcome(self, decision_id: str, default: Dict[str, Any]) -> Dict[str, Any]:
        """Get outcome for a specific decision"""
        for outcome in self.decision_outcomes:
            if outcome.decision_id == decision_id:
                return {
                    "success": outcome.success,
                    "execution_time_ms": outcome.execution_time_ms,
                    "deviation_from_expected": outcome.deviation_from_expected
                }
        return default

    def _analyze_business_rules(self, category: DecisionCategory, context: DecisionContext) -> Dict[str, Any]:
        """Analyze compliance with business rules"""
        rules = self.business_rules
        system_state = context.system_state

        compliance_issues = []

        # Check maintenance window constraints
        current_hour = datetime.now().hour
        if not (2 <= current_hour <= 4) and category == DecisionCategory.PREDICTIVE_ACTION:
            compliance_issues.append("Maintenance actions outside maintenance window")

        # Check cost constraints
        current_costs = system_state.get("cost_metrics", {}).get("monthly_cost", 0)
        if current_costs > rules["cost_thresholds"]["alert_threshold"]:
            compliance_issues.append("Approaching cost limit")

        # Check performance SLA
        current_performance = system_state.get("performance_metrics", {})
        if current_performance.get("uptime", 100) < float(rules["performance_sla"]["uptime"].rstrip('%')):
            compliance_issues.append("SLA violation detected")

        return {
            "compliant": len(compliance_issues) == 0,
            "compliance_issues": compliance_issues,
            "severity": "high" if len(compliance_issues) > 2 else "medium" if compliance_issues else "low"
        }

    def _assess_risks(self, category: DecisionCategory, context: DecisionContext) -> Dict[str, Any]:
        """Assess risks associated with decision category"""
        system_state = context.system_state
        resource_availability = self._analyze_resource_availability(context)

        risk_factors = []
        risk_level = "low"

        # Assess system stability risk
        health_score = system_state.get("ai_control_status", {}).get("system_health_score", 0.5)
        if health_score < 0.5:
            risk_factors.append("System in unstable state")
            risk_level = "high"
        elif health_score < 0.7:
            risk_factors.append("System health degraded")
            risk_level = "medium"

        # Assess resource risk
        constrained_resources = resource_availability.get("constrained_resources", [])
        if constrained_resources:
            risk_factors.append(f"Constrained resources: {', '.join(constrained_resources)}")
            risk_level = max(risk_level, "medium")

        # Assess time risk
        time_analysis = self._analyze_time_constraints(context)
        if time_analysis["time_sensitivity"] == "critical" and time_analysis["optimal_execution_time"] != "immediate":
            risk_factors.append("Critical timing constraints")
            risk_level = "high"

        return {
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "risk_score": self._calculate_risk_score(risk_level, len(risk_factors))
        }

    def _calculate_risk_score(self, risk_level: str, factor_count: int) -> float:
        """Calculate numerical risk score"""
        level_scores = {"low": 0.2, "medium": 0.5, "high": 0.8}
        base_score = level_scores.get(risk_level, 0.5)

        # Increase score with more risk factors
        factor_penalty = min(factor_count * 0.1, 0.3)

        return min(1.0, base_score + factor_penalty)

    def _generate_decision_factors(self, category: DecisionCategory, context: DecisionContext,
                                 analysis_result: Dict[str, Any]) -> List[DecisionFactor]:
        """Generate factors that influence the decision"""
        factors = []

        # System health factor
        health_score = analysis_result["system_health"]["health_score"]
        factors.append(DecisionFactor(
            name="system_health",
            weight=self.learning_weights["system_state"],
            value=health_score,
            normalized_value=health_score,
            category="system",
            description="Current system health score"
        ))

        # Resource availability factor
        resource_analysis = analysis_result["resource_availability"]
        resource_score = self._calculate_resource_score(resource_analysis)
        factors.append(DecisionFactor(
            name="resource_availability",
            weight=self.learning_weights["resource_availability"],
            value=resource_score,
            normalized_value=resource_score,
            category="resources",
            description="Available system resources"
        ))

        # Historical performance factor
        historical_analysis = analysis_result["historical_patterns"]
        if historical_analysis["sufficient_data"]:
            historical_score = historical_analysis["success_rate"]
            factors.append(DecisionFactor(
                name="historical_performance",
                weight=self.learning_weights["historical_success"],
                value=historical_score,
                normalized_value=historical_score,
                category="learning",
                description="Historical success rate for similar decisions"
            ))

        # Time criticality factor
        time_analysis = analysis_result["time_constraints"]
        time_score = self._calculate_time_score(time_analysis)
        factors.append(DecisionFactor(
            name="time_criticality",
            weight=self.learning_weights["time_criticality"],
            value=time_score,
            normalized_value=time_score,
            category="timing",
            description="Time sensitivity and constraints"
        ))

        # Business rule compliance factor
        business_analysis = analysis_result["business_rules"]
        compliance_score = 1.0 if business_analysis["compliant"] else 0.3
        factors.append(DecisionFactor(
            name="business_compliance",
            weight=0.2,
            value=compliance_score,
            normalized_value=compliance_score,
            category="business",
            description="Compliance with business rules"
        ))

        # Risk assessment factor
        risk_analysis = analysis_result["risk_assessment"]
        risk_score = 1.0 - risk_analysis["risk_score"]
        factors.append(DecisionFactor(
            name="risk_assessment",
            weight=0.15,
            value=risk_score,
            normalized_value=risk_score,
            category="risk",
            description="Risk assessment score"
        ))

        # Category-specific factors
        category_factors = self._generate_category_specific_factors(category, context, analysis_result)
        factors.extend(category_factors)

        return factors

    def _calculate_resource_score(self, resource_analysis: Dict[str, Any]) -> float:
        """Calculate resource availability score"""
        availability_data = resource_analysis.get("resource_availability", {})

        if not availability_data:
            return 0.5

        # Calculate average availability percentage
        total_available = sum(data.get("available", 0) for data in availability_data.values())
        total_max = sum(data.get("max_usage", 100) for data in availability_data.values())

        if total_max == 0:
            return 0.5

        return min(1.0, total_available / total_max)

    def _calculate_time_score(self, time_analysis: Dict[str, Any]) -> float:
        """Calculate time constraint score"""
        sensitivity = time_analysis.get("time_sensitivity", "normal")
        optimal_time = time_analysis.get("optimal_execution_time", "scheduled")

        if sensitivity == "critical" and optimal_time == "immediate":
            return 1.0
        elif sensitivity == "critical":
            return 0.5
        elif optimal_time == "maintenance_window":
            return 0.9
        elif optimal_time == "off_hours":
            return 0.8
        else:
            return 0.6

    def _generate_category_specific_factors(self, category: DecisionCategory, context: DecisionContext,
                                          analysis_result: Dict[str, Any]) -> List[DecisionFactor]:
        """Generate factors specific to decision category"""
        factors = []

        if category == DecisionCategory.SERVICE_MANAGEMENT:
            # Service-specific factors
            service_health = analysis_result["system_health"].get("unhealthy_services", [])
            service_impact = min(1.0, len(service_health) * 0.3)
            factors.append(DecisionFactor(
                name="service_impact",
                weight=0.3,
                value=service_impact,
                normalized_value=service_impact,
                category="service",
                description="Impact of unhealthy services"
            ))

        elif category == DecisionCategory.PERFORMANCE_TUNING:
            # Performance-specific factors
            performance_metrics = context.system_state.get("performance_metrics", {})
            cpu_usage = performance_metrics.get("cpu_percent", 50)
            memory_usage = performance_metrics.get("memory_percent", 50)

            performance_pressure = max(cpu_usage, memory_usage) / 100.0
            factors.append(DecisionFactor(
                name="performance_pressure",
                weight=0.4,
                value=performance_pressure,
                normalized_value=performance_pressure,
                category="performance",
                description="System performance pressure"
            ))

        elif category == DecisionCategory.COST_OPTIMIZATION:
            # Cost-specific factors
            cost_metrics = context.system_state.get("cost_metrics", {})
            current_cost = cost_metrics.get("monthly_cost", 0)
            cost_threshold = self.business_rules["cost_thresholds"]["monthly_limit"]

            cost_pressure = min(1.0, current_cost / cost_threshold)
            factors.append(DecisionFactor(
                name="cost_pressure",
                weight=0.5,
                value=cost_pressure,
                normalized_value=cost_pressure,
                category="cost",
                description="Current cost pressure relative to limit"
            ))

        return factors

    def _calculate_decision_confidence(self, factors: List[DecisionFactor], category: DecisionCategory) -> float:
        """Calculate overall decision confidence"""
        if not factors:
            return 0.5

        # Calculate weighted average of factor values
        total_weight = sum(factor.weight for factor in factors)
        weighted_sum = sum(factor.weight * factor.normalized_value for factor in factors)

        base_confidence = weighted_sum / total_weight if total_weight > 0 else 0.5

        # Adjust based on factor count and consistency
        factor_count_adjustment = min(0.1, len(factors) * 0.02)

        # Calculate factor consistency (how aligned the factors are)
        if len(factors) > 1:
            values = [factor.normalized_value for factor in factors]
            consistency = 1.0 - statistics.stdev(values) if len(values) > 1 else 1.0
            consistency_adjustment = consistency * 0.1
        else:
            consistency_adjustment = 0.0

        confidence = base_confidence + factor_count_adjustment + consistency_adjustment

        return max(0.0, min(1.0, confidence))

    def _generate_decision_alternatives(self, category: DecisionCategory, context: DecisionContext,
                                      factors: List[DecisionFactor]) -> List[str]:
        """Generate alternative actions for the decision"""
        alternatives = []

        if category == DecisionCategory.SYSTEM_OPTIMIZATION:
            alternatives = [
                "optimize_performance",
                "cleanup_resources",
                "rebalance_load",
                "scale_resources"
            ]
        elif category == DecisionCategory.ERROR_RECOVERY:
            alternatives = [
                "restart_service",
                "rollback_changes",
                "restore_backup",
                "escalate_to_human"
            ]
        elif category == DecisionCategory.SERVICE_MANAGEMENT:
            alternatives = [
                "restart_service",
                "scale_service",
                "maintenance_mode",
                "degrade_service"
            ]
        elif category == DecisionCategory.RESOURCE_MANAGEMENT:
            alternatives = [
                "allocate_more_resources",
                "optimize_usage",
                "implement_caching",
                "schedule_cleanup"
            ]
        else:
            alternatives = ["proceed", "delay_action", "escalate", "monitor_only"]

        # Filter alternatives based on resource constraints
        filtered_alternatives = []
        for alternative in alternatives:
            if self._is_alternative_feasible(alternative, context, factors):
                filtered_alternatives.append(alternative)

        return filtered_alternatives if filtered_alternatives else alternatives[:3]

    def _is_alternative_feasible(self, alternative: str, context: DecisionContext,
                                factors: List[DecisionFactor]) -> bool:
        """Check if alternative action is feasible given constraints"""
        resource_availability = next((f for f in factors if f.name == "resource_availability"), None)

        if resource_availability and resource_availability.normalized_value < 0.3:
            # Low resources - avoid resource-intensive actions
            resource_intensive_actions = ["scale_resources", "allocate_more_resources", "implement_caching"]
            if alternative in resource_intensive_actions:
                return False

        # Check time constraints
        time_analysis = self._analyze_time_constraints(context)
        if time_analysis["time_sensitivity"] == "critical":
            # Critical time - avoid slow actions
            slow_actions = ["schedule_cleanup", "maintenance_mode"]
            if alternative in slow_actions:
                return False

        return True

    def _select_best_action(self, category: DecisionCategory, factors: List[DecisionFactor],
                           alternatives: List[str]) -> Tuple[str, List[str]]:
        """Select the best action from alternatives"""
        if not alternatives:
            return "no_action", ["No feasible alternatives available"]

        # Score each alternative based on factors
        action_scores = {}
        for alternative in alternatives:
            score = self._score_alternative(alternative, category, factors)
            action_scores[alternative] = score

        # Select best action
        best_action = max(action_scores.items(), key=lambda x: x[1])[0]

        # Generate reasoning
        reasoning = [
            f"Selected action: {best_action}",
            f"Score: {action_scores[best_action]:.2f}",
            f"Considered {len(alternatives)} alternatives"
        ]

        # Add factor-specific reasoning
        for factor in factors:
            if factor.normalized_value > 0.8 or factor.normalized_value < 0.3:
                reasoning.append(f"{factor.name}: {'High' if factor.normalized_value > 0.8 else 'Low'} ({factor.normalized_value:.2f})")

        return best_action, reasoning

    def _score_alternative(self, alternative: str, category: DecisionCategory,
                          factors: List[DecisionFactor]) -> float:
        """Score an alternative action based on decision factors"""
        base_score = 0.5

        # Category-specific scoring
        if category == DecisionCategory.SYSTEM_OPTIMIZATION:
            if alternative == "optimize_performance":
                performance_factor = next((f for f in factors if "performance" in f.name), None)
                if performance_factor:
                    base_score += performance_factor.normalized_value * 0.3

            elif alternative == "cleanup_resources":
                resource_factor = next((f for f in factors if "resource" in f.name), None)
                if resource_factor:
                    base_score += (1.0 - resource_factor.normalized_value) * 0.3

        elif category == DecisionCategory.ERROR_RECOVERY:
            if alternative == "restart_service":
                health_factor = next((f for f in factors if f.name == "system_health"), None)
                if health_factor and health_factor.normalized_value > 0.7:
                    base_score += 0.2

        # General scoring adjustments
        risk_factor = next((f for f in factors if "risk" in f.name), None)
        if risk_factor:
            base_score += risk_factor.normalized_value * 0.2

        time_factor = next((f for f in factors if "time" in f.name), None)
        if time_factor:
            base_score += time_factor.normalized_value * 0.1

        return max(0.0, min(1.0, base_score))

    def _determine_priority(self, category: DecisionCategory, confidence: float,
                           context: DecisionContext) -> DecisionPriority:
        """Determine decision priority"""
        # High-risk categories get higher priority
        if category in [DecisionCategory.ERROR_RECOVERY, DecisionCategory.SECURITY_RESPONSE]:
            return DecisionPriority.CRITICAL

        # Low confidence decisions may need review
        if confidence < 0.4:
            return DecisionPriority.LOW

        # Time-sensitive decisions
        time_analysis = self._analyze_time_constraints(context)
        if time_analysis["time_sensitivity"] == "critical":
            return DecisionPriority.CRITICAL

        # System health considerations
        health_analysis = self._analyze_system_health(context)
        if health_analysis["overall_status"] == "unhealthy":
            return DecisionPriority.HIGH

        return DecisionPriority.MEDIUM

    def _determine_execution_permissions(self, category: DecisionCategory, confidence: float,
                                       priority: DecisionPriority, context: DecisionContext) -> Tuple[bool, bool]:
        """Determine if decision can be auto-executed and requires approval"""
        auto_execute = False
        requires_approval = True

        # High confidence + appropriate category = auto-execute
        if confidence >= self.decision_thresholds["auto_execute"]:
            if category in [DecisionCategory.SYSTEM_OPTIMIZATION, DecisionCategory.PERFORMANCE_TUNING]:
                auto_execute = True
                requires_approval = False

        # Critical decisions always require approval
        if priority == DecisionPriority.CRITICAL:
            auto_execute = False
            requires_approval = True

        # Low confidence decisions require approval
        if confidence < self.decision_thresholds["medium_confidence"]:
            auto_execute = False
            requires_approval = True

        # Business rule compliance issues require approval
        business_analysis = self._analyze_business_rules(category, context)
        if not business_analysis["compliant"]:
            auto_execute = False
            requires_approval = True

        return auto_execute, requires_approval

    def _create_execution_plan(self, action: str, category: DecisionCategory,
                              context: DecisionContext) -> Dict[str, Any]:
        """Create execution plan for the decision"""
        plan = {
            "steps": [],
            "estimated_duration": self._estimate_execution_duration(action, category),
            "resource_requirements": self._estimate_resource_requirements(action, category),
            "rollback_plan": self._create_rollback_plan(action, category),
            "verification_steps": self._create_verification_steps(action, category)
        }

        # Add specific execution steps based on action
        if action == "restart_service":
            plan["steps"] = [
                "Verify service status",
                "Prepare service restart",
                "Execute service restart",
                "Verify service health",
                "Monitor for 5 minutes"
            ]
        elif action == "optimize_performance":
            plan["steps"] = [
                "Analyze performance bottlenecks",
                "Generate optimization recommendations",
                "Apply optimizations",
                "Monitor performance impact",
                "Rollback if necessary"
            ]
        else:
            plan["steps"] = [
                "Prepare execution environment",
                f"Execute {action}",
                "Monitor results",
                "Verify success criteria"
            ]

        return plan

    def _estimate_execution_duration(self, action: str, category: DecisionCategory) -> float:
        """Estimate execution duration in seconds"""
        duration_map = {
            "restart_service": 30.0,
            "optimize_performance": 120.0,
            "cleanup_resources": 60.0,
            "scale_resources": 300.0,
            "restore_backup": 600.0
        }

        return duration_map.get(action, 60.0)

    def _estimate_resource_requirements(self, action: str, category: DecisionCategory) -> Dict[str, Any]:
        """Estimate resource requirements for execution"""
        requirements = {
            "cpu_percent": 20.0,
            "memory_mb": 100,
            "disk_mb": 50,
            "network_bandwidth_mbps": 1.0
        }

        if action == "scale_resources":
            requirements["cpu_percent"] = 50.0
            requirements["memory_mb"] = 500
        elif action == "optimize_performance":
            requirements["cpu_percent"] = 40.0
            requirements["memory_mb"] = 200

        return requirements

    def _create_rollback_plan(self, action: str, category: DecisionCategory) -> Dict[str, Any]:
        """Create rollback plan for the decision"""
        rollback_plan = {
            "can_rollback": True,
            "rollback_steps": [],
            "estimated_rollback_time": 30.0
        }

        if action == "restart_service":
            rollback_plan["rollback_steps"] = [
                "Stop restarted service",
                "Restore previous configuration",
                "Start service normally"
            ]
        elif action == "optimize_performance":
            rollback_plan["rollback_steps"] = [
                "Revert performance optimizations",
                "Restore original configuration",
                "Verify system stability"
            ]
        else:
            rollback_plan["can_rollback"] = False
            rollback_plan["rollback_steps"] = ["No rollback available"]

        return rollback_plan

    def _create_verification_steps(self, action: str, category: DecisionCategory) -> List[str]:
        """Create verification steps for decision execution"""
        return [
            "Verify action completion",
            "Check system health",
            "Monitor performance impact",
            "Validate expected outcomes",
            "Confirm no regressions"
        ]

    def _estimate_expected_outcome(self, action: str, category: DecisionCategory,
                                  factors: List[DecisionFactor]) -> Dict[str, Any]:
        """Estimate expected outcome of the decision"""
        outcome = {
            "success_probability": 0.8,
            "expected_benefits": [],
            "estimated_impact": "medium",
            "resource_utilization_change": 0.0
        }

        if category == DecisionCategory.SYSTEM_OPTIMIZATION:
            outcome["expected_benefits"] = ["Improved system performance", "Better resource utilization"]
            outcome["estimated_impact"] = "high"
            outcome["resource_utilization_change"] = -0.15  # 15% reduction

        elif category == DecisionCategory.ERROR_RECOVERY:
            outcome["expected_benefits"] = ["Resolved error", "Restored service functionality"]
            outcome["estimated_impact"] = "critical"
            outcome["success_probability"] = 0.9

        elif category == DecisionCategory.PERFORMANCE_TUNING:
            outcome["expected_benefits"] = ["Faster response times", "Improved user experience"]
            outcome["estimated_impact"] = "medium"
            outcome["resource_utilization_change"] = -0.10

        # Adjust based on factors
        confidence = sum(factor.weight * factor.normalized_value for factor in factors) / sum(f.weight for f in factors)
        outcome["success_probability"] = min(0.95, confidence)

        return outcome

    def _identify_risks(self, action: str, category: DecisionCategory, context: DecisionContext,
                        factors: List[DecisionFactor]) -> List[str]:
        """Identify risks associated with the decision"""
        risks = []

        # Common risks
        risks.append("Execution failure")
        risks.append("Unexpected side effects")

        # Category-specific risks
        if category == DecisionCategory.SERVICE_MANAGEMENT:
            risks.extend(["Service downtime", "Data loss", "User impact"])
        elif category == DecisionCategory.RESOURCE_MANAGEMENT:
            risks.extend(["Resource exhaustion", "Cost overruns", "Performance degradation"])
        elif category == DecisionCategory.ERROR_RECOVERY:
            risks.extend(["Incomplete recovery", "Data corruption", "Extended downtime"])

        # Context-specific risks
        health_analysis = self._analyze_system_health(context)
        if health_analysis["overall_status"] == "unhealthy":
            risks.append("Compounding existing system issues")

        risk_analysis = self._assess_risks(category, context)
        if risk_analysis["risk_level"] == "high":
            risks.append("High-risk execution environment")

        return risks

    def _record_decision(self, decision: AIDecision):
        """Record decision for future learning"""
        self.decision_history.append(decision)

        # Keep only recent decisions (last 1000)
        if len(self.decision_history) > 1000:
            self.decision_history = self.decision_history[-1000:]

        # Update decision patterns
        self._update_decision_patterns(decision)

    def _update_decision_patterns(self, decision: AIDecision):
        """Update decision pattern analysis"""
        category = decision.category.value
        action = decision.action

        if category not in self.decision_patterns:
            self.decision_patterns[category] = {
                "total_decisions": 0,
                "successful_decisions": 0,
                "actions": {},
                "avg_confidence": 0.0,
                "success_rate": 0.0
            }

        pattern = self.decision_patterns[category]
        pattern["total_decisions"] += 1

        if action not in pattern["actions"]:
            pattern["actions"][action] = {"count": 0, "successful": 0}

        pattern["actions"][action]["count"] += 1

        # Update confidence average
        total = pattern["total_decisions"]
        current_avg = pattern["avg_confidence"]
        pattern["avg_confidence"] = ((current_avg * (total - 1)) + decision.confidence) / total

    def _update_decision_metrics(self, decision: AIDecision):
        """Update decision performance metrics"""
        self.performance_metrics["total_decisions"] += 1

        if decision.auto_execute:
            self.performance_metrics["auto_executed"] += 1

        # Update average confidence
        total = self.performance_metrics["total_decisions"]
        current_avg = self.performance_metrics["avg_confidence"]
        self.performance_metrics["avg_confidence"] = ((current_avg * (total - 1)) + decision.confidence) / total

    def record_decision_outcome(self, decision_id: str, success: bool, actual_outcome: Dict[str, Any],
                              execution_time_ms: float):
        """Record the outcome of a decision execution"""
        # Find the decision
        decision = next((d for d in self.decision_history if d.id == decision_id), None)
        if not decision:
            logger.warning(f"Decision {decision_id} not found for outcome recording")
            return

        # Calculate deviation from expected
        expected_outcome = decision.expected_outcome
        deviation = self._calculate_outcome_deviation(expected_outcome, actual_outcome)

        # Create outcome record
        outcome = DecisionOutcome(
            decision_id=decision_id,
            success=success,
            actual_outcome=actual_outcome,
            execution_time_ms=execution_time_ms,
            deviation_from_expected=deviation,
            lessons_learned=self._generate_lessons_learned(decision, success, actual_outcome),
            timestamp=datetime.now()
        )

        self.decision_outcomes.append(outcome)

        # Update decision patterns
        self._update_patterns_with_outcome(decision, success)

        # Update performance metrics
        self._update_metrics_with_outcome(success)

        # Update learning weights based on outcome
        self._update_learning_weights(decision, success, outcome)

        logger.info(f"Decision outcome recorded: {decision_id} - {'Success' if success else 'Failed'}")

    def _calculate_outcome_deviation(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> float:
        """Calculate deviation between expected and actual outcomes"""
        # Simple deviation calculation - can be enhanced
        expected_success = expected.get("success_probability", 0.8)
        actual_success = 1.0 if actual.get("success", False) else 0.0

        return abs(expected_success - actual_success)

    def _generate_lessons_learned(self, decision: AIDecision, success: bool,
                                 actual_outcome: Dict[str, Any]) -> List[str]:
        """Generate lessons learned from decision outcome"""
        lessons = []

        if success:
            lessons.append(f"Successful execution of {decision.action}")
            if decision.confidence > 0.8:
                lessons.append("High confidence led to successful outcome")
        else:
            lessons.append(f"Failed execution of {decision.action}")
            if decision.confidence > 0.8:
                lessons.append("Overconfidence in unsuccessful decision")
            if not decision.auto_execute:
                lessons.append("Manual approval didn't prevent failure")

        # Factor-specific lessons
        for factor in decision.factors:
            if factor.normalized_value < 0.3 and not success:
                lessons.append(f"Low {factor.name} may have contributed to failure")
            elif factor.normalized_value > 0.8 and success:
                lessons.append(f"High {factor.name} contributed to success")

        return lessons

    def _update_patterns_with_outcome(self, decision: AIDecision, success: bool):
        """Update decision patterns with outcome data"""
        category = decision.category.value
        action = decision.action

        if category in self.decision_patterns:
            pattern = self.decision_patterns[category]
            if success:
                pattern["successful_decisions"] += 1

            if action in pattern["actions"]:
                pattern["actions"][action]["successful"] += 1

            # Update success rate
            total = pattern["total_decisions"]
            successful = pattern["successful_decisions"]
            pattern["success_rate"] = successful / total if total > 0 else 0.0

    def _update_metrics_with_outcome(self, success: bool):
        """Update performance metrics with outcome"""
        if success:
            self.performance_metrics["successful_decisions"] += 1

        total = self.performance_metrics["total_decisions"]
        successful = self.performance_metrics["successful_decisions"]
        self.performance_metrics["avg_accuracy"] = successful / total if total > 0 else 0.0

    def _update_learning_weights(self, decision: AIDecision, success: bool, outcome: DecisionOutcome):
        """Update learning weights based on decision outcomes"""
        # Adjust weights based on factor performance
        for factor in decision.factors:
            factor_name = factor.name

            # Map factor to learning weight category
            weight_mapping = {
                "system_health": "system_state",
                "resource_availability": "resource_availability",
                "historical_performance": "historical_success",
                "time_criticality": "time_criticality"
            }

            if factor_name in weight_mapping:
                weight_category = weight_mapping[factor_name]

                # Adjust weight based on factor's correlation with success
                correlation = 1.0 if success else 0.0
                adjustment = (factor.normalized_value - 0.5) * correlation * 0.01

                self.learning_weights[weight_category] = max(0.1, min(0.5,
                    self.learning_weights[weight_category] + adjustment))

        # Normalize weights
        total_weight = sum(self.learning_weights.values())
        for key in self.learning_weights:
            self.learning_weights[key] /= total_weight

    async def make_autonomous_decision(self, situation: Dict[str, Any]) -> AIDecision:
        """Make an autonomous decision based on current system state"""
        # Determine decision category from situation
        category = self._determine_decision_category(situation)

        # Create decision context
        context = self._create_decision_context(situation)

        # Make decision
        decision = await self.make_decision(category, context)

        # Auto-execute if appropriate
        if decision.auto_execute:
            logger.info(f"Auto-executing decision: {decision.action}")
            await self._execute_decision(decision)

        return decision

    def _determine_decision_category(self, situation: Dict[str, Any]) -> DecisionCategory:
        """Determine decision category from situation description"""
        situation_type = situation.get("type", "").lower()

        if "error" in situation_type or "failure" in situation_type:
            return DecisionCategory.ERROR_RECOVERY
        elif "performance" in situation_type or "slow" in situation_type:
            return DecisionCategory.PERFORMANCE_TUNING
        elif "service" in situation_type:
            return DecisionCategory.SERVICE_MANAGEMENT
        elif "resource" in situation_type or "memory" in situation_type or "cpu" in situation_type:
            return DecisionCategory.RESOURCE_MANAGEMENT
        elif "cost" in situation_type:
            return DecisionCategory.COST_OPTIMIZATION
        elif "security" in situation_type:
            return DecisionCategory.SECURITY_RESPONSE
        else:
            return DecisionCategory.SYSTEM_OPTIMIZATION

    def _create_decision_context(self, situation: Dict[str, Any]) -> DecisionContext:
        """Create decision context from situation"""
        system_status = get_system_status_for_ai()

        return DecisionContext(
            system_state=system_status,
            historical_data=situation.get("historical_data", {}),
            user_preferences=situation.get("user_preferences", {}),
            business_rules=self.business_rules,
            time_constraints=situation.get("time_constraints", {"sensitivity": "normal"}),
            resource_constraints=self.resource_constraints
        )

    async def _execute_decision(self, decision: AIDecision):
        """Execute a decision action"""
        try:
            # Map decision to AI controller command
            command_mapping = {
                "restart_service": ("service_control", "restart_service"),
                "optimize_performance": ("performance_optimization", "optimize_performance"),
                "cleanup_resources": ("resource_management", "cleanup_cache"),
                "scale_resources": ("resource_management", "scale_resources")
            }

            action = decision.action
            if action in command_mapping:
                command_type, command_action = command_mapping[action]

                # Execute through AI controller
                from duckbot.core.ai_system_controller import process_ai_command
                result = await process_ai_command(
                    command_type=command_type,
                    action=command_action,
                    parameters=decision.execution_plan.get("resource_requirements", {}),
                    auto_execute=True
                )

                # Record outcome
                self.record_decision_outcome(
                    decision_id=decision.id,
                    success=result.get("success", False),
                    actual_outcome=result,
                    execution_time_ms=result.get("execution_time_ms", 0)
                )

                return result

            else:
                logger.warning(f"Unknown decision action: {action}")
                return {"success": False, "error": f"Unknown action: {action}"}

        except Exception as e:
            logger.error(f"Error executing decision {decision.id}: {e}")
            self.record_decision_outcome(
                decision_id=decision.id,
                success=False,
                actual_outcome={"error": str(e)},
                execution_time_ms=0
            )
            return {"success": False, "error": str(e)}

    def get_decision_insights(self) -> Dict[str, Any]:
        """Get insights about decision making performance"""
        return {
            "performance_metrics": self.performance_metrics,
            "decision_patterns": self.decision_patterns,
            "learning_weights": self.learning_weights,
            "recent_decisions": [
                {
                    "id": d.id,
                    "category": d.category.value,
                    "action": d.action,
                    "confidence": d.confidence,
                    "success": self._get_decision_outcome(d.id, {}).get("success", None),
                    "timestamp": d.timestamp.isoformat()
                }
                for d in self.decision_history[-10:]
            ],
            "recommendations": self._generate_decision_recommendations()
        }

    def _generate_decision_recommendations(self) -> List[str]:
        """Generate recommendations for improving decision making"""
        recommendations = []

        # Performance-based recommendations
        if self.performance_metrics["avg_accuracy"] < 0.7:
            recommendations.append("Consider reviewing decision criteria and thresholds")

        if self.performance_metrics["avg_confidence"] < 0.6:
            recommendations.append("Decision confidence is low - may need more data")

        # Pattern-based recommendations
        for category, pattern in self.decision_patterns.items():
            if pattern["success_rate"] < 0.5 and pattern["total_decisions"] > 5:
                recommendations.append(f"Low success rate for {category} decisions - review approach")

        # Autonomy recommendations
        if self.performance_metrics["auto_executed"] / max(1, self.performance_metrics["total_decisions"]) < 0.3:
            recommendations.append("Consider increasing autonomy for routine decisions")

        return recommendations

# Global decision maker instance
_decision_maker = None

def get_decision_maker() -> AIDecisionMaker:
    """Get the global decision maker instance"""
    global _decision_maker
    if _decision_maker is None:
        _decision_maker = AIDecisionMaker()
    return _decision_maker

async def make_ai_decision(category: str, situation: Dict[str, Any]) -> Dict[str, Any]:
    """Make an AI decision for the given situation"""
    decision_maker = get_decision_maker()

    decision_category = DecisionCategory(category)
    context = decision_maker._create_decision_context(situation)

    decision = await decision_maker.make_decision(decision_category, context)

    return {
        "decision_id": decision.id,
        "action": decision.action,
        "confidence": decision.confidence,
        "priority": decision.priority.value,
        "reasoning": decision.reasoning,
        "auto_execute": decision.auto_execute,
        "requires_approval": decision.requires_approval,
        "expected_outcome": decision.expected_outcome,
        "risks": decision.risks,
        "execution_plan": decision.execution_plan
    }

async def make_autonomous_decision(situation: Dict[str, Any]) -> Dict[str, Any]:
    """Make an autonomous decision based on system state"""
    decision_maker = get_decision_maker()
    decision = await decision_maker.make_autonomous_decision(situation)

    return {
        "decision_id": decision.id,
        "action": decision.action,
        "confidence": decision.confidence,
        "executed": decision.auto_execute,
        "success": decision.auto_execute,  # If auto-executed, assume success
        "timestamp": decision.timestamp.isoformat()
    }

def get_decision_insights() -> Dict[str, Any]:
    """Get decision making insights and analytics"""
    decision_maker = get_decision_maker()
    return decision_maker.get_decision_insights()

if __name__ == "__main__":
    # Test the AI decision maker
    print("Testing DuckBot AI Decision Maker")

    async def test_decision_maker():
        decision_maker = get_decision_maker()

        # Test decision making
        print("\nTesting decision making...")
        situation = {
            "type": "performance",
            "description": "System performance degradation",
            "time_constraints": {"sensitivity": "high"},
            "user_preferences": {"performance_priority": "high"}
        }

        result = await make_ai_decision("performance_tuning", situation)
        print(f"Decision made: {result['action']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Auto-execute: {result['auto_execute']}")

        # Test autonomous decision
        print("\nTesting autonomous decision...")
        autonomous_result = await make_autonomous_decision(situation)
        print(f"Autonomous decision: {autonomous_result['action']}")
        print(f"Executed: {autonomous_result['executed']}")

        # Get insights
        print("\nGetting decision insights...")
        insights = get_decision_insights()
        print(f"Total decisions: {insights['performance_metrics']['total_decisions']}")
        print(f"Success rate: {insights['performance_metrics']['avg_accuracy']:.2%}")

        print("\nAI Decision Maker test completed successfully!")

    asyncio.run(test_decision_maker())