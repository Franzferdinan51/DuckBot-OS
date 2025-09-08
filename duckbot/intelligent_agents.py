"""
DuckBot Intelligent Agent Framework
SIM.ai-inspired adaptive agents for intelligent decision-making and learning
"""

import json
import time
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)

class AgentType(Enum):
    """Types of intelligent agents in the DuckBot ecosystem"""
    MARKET_ANALYZER = "market_analyzer"
    DISCORD_MODERATOR = "discord_moderator" 
    WORKFLOW_OPTIMIZER = "workflow_optimizer"
    USER_BEHAVIOR_PREDICTOR = "user_behavior_predictor"
    RESPONSE_OPTIMIZER = "response_optimizer"
    DECISION_MAKER = "decision_maker"
    CODE_ANALYZER = "code_analyzer"
    COST_OPTIMIZER = "cost_optimizer"

class AgentCapability(Enum):
    """Capabilities that agents can have"""
    LEARNING = "learning"
    PREDICTION = "prediction"
    OPTIMIZATION = "optimization"
    ANALYSIS = "analysis"
    DECISION_MAKING = "decision_making"
    CONTEXT_AWARENESS = "context_awareness"
    MEMORY = "memory"
    ADAPTATION = "adaptation"

@dataclass
class AgentContext:
    """Context information for agent decision-making"""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: float = None
    environment: Dict[str, Any] = None
    history: List[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.environment is None:
            self.environment = {}
        if self.history is None:
            self.history = []
        if self.metadata is None:
            self.metadata = {}

@dataclass  
class AgentDecision:
    """Result of agent decision-making"""
    action: str
    confidence: float
    reasoning: str
    data: Dict[str, Any]
    agent_type: str
    timestamp: float = None
    context_hash: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.context_hash is None:
            self.context_hash = hashlib.md5(str(self.data).encode()).hexdigest()[:8]

@dataclass
class LearningData:
    """Data structure for agent learning"""
    input_data: Dict[str, Any]
    output_data: Dict[str, Any] 
    success_metric: float
    feedback: Optional[str]
    context: AgentContext
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

class BaseIntelligentAgent(ABC):
    """Base class for all intelligent agents"""
    
    def __init__(self, agent_type: AgentType, capabilities: List[AgentCapability]):
        self.agent_type = agent_type
        self.capabilities = capabilities
        self.learning_history: List[LearningData] = []
        self.context_memory: Dict[str, Any] = {}
        self.performance_metrics = {
            "decisions_made": 0,
            "success_rate": 0.0,
            "learning_iterations": 0,
            "avg_confidence": 0.0
        }
        self.decision_threshold = 0.7  # Minimum confidence for autonomous decisions
        
    @abstractmethod
    async def analyze(self, input_data: Dict[str, Any], context: AgentContext) -> AgentDecision:
        """Analyze input and make intelligent decision"""
        pass
    
    @abstractmethod
    async def learn_from_feedback(self, learning_data: LearningData) -> bool:
        """Learn from feedback to improve future decisions"""
        pass
    
    def has_capability(self, capability: AgentCapability) -> bool:
        """Check if agent has specific capability"""
        return capability in self.capabilities
    
    def update_context_memory(self, key: str, value: Any):
        """Update agent's context memory"""
        self.context_memory[key] = {
            "value": value,
            "timestamp": time.time()
        }
    
    def get_context_memory(self, key: str, max_age: float = 3600) -> Optional[Any]:
        """Get value from context memory with age check"""
        if key in self.context_memory:
            data = self.context_memory[key]
            if time.time() - data["timestamp"] < max_age:
                return data["value"]
        return None
    
    def update_performance_metrics(self, decision: AgentDecision, success: bool):
        """Update agent performance metrics"""
        self.performance_metrics["decisions_made"] += 1
        
        # Update success rate (running average)
        current_rate = self.performance_metrics["success_rate"]
        total_decisions = self.performance_metrics["decisions_made"]
        new_rate = ((current_rate * (total_decisions - 1)) + (1.0 if success else 0.0)) / total_decisions
        self.performance_metrics["success_rate"] = new_rate
        
        # Update average confidence
        current_conf = self.performance_metrics["avg_confidence"]
        new_conf = ((current_conf * (total_decisions - 1)) + decision.confidence) / total_decisions
        self.performance_metrics["avg_confidence"] = new_conf
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get detailed performance report"""
        return {
            "agent_type": self.agent_type.value,
            "capabilities": [cap.value for cap in self.capabilities],
            "metrics": self.performance_metrics.copy(),
            "learning_data_points": len(self.learning_history),
            "context_memory_size": len(self.context_memory),
            "decision_threshold": self.decision_threshold
        }


class MarketAnalyzerAgent(BaseIntelligentAgent):
    """Intelligent agent for market analysis and prediction"""
    
    def __init__(self):
        super().__init__(
            AgentType.MARKET_ANALYZER,
            [AgentCapability.ANALYSIS, AgentCapability.PREDICTION, AgentCapability.LEARNING]
        )
        self.market_patterns = {}
        self.prediction_accuracy = {}
    
    async def analyze(self, input_data: Dict[str, Any], context: AgentContext) -> AgentDecision:
        """Analyze market data and make predictions"""
        market_data = input_data.get("market_data", {})
        user_preferences = input_data.get("user_preferences", {})
        
        # Analyze patterns
        patterns = await self._detect_patterns(market_data)
        
        # Generate prediction
        prediction = await self._generate_prediction(patterns, user_preferences, context)
        
        # Calculate confidence based on historical accuracy
        confidence = self._calculate_confidence(patterns, context)
        
        reasoning = f"Detected patterns: {', '.join(patterns.keys())}. " \
                   f"Historical accuracy: {self.performance_metrics['success_rate']:.2%}. " \
                   f"Market volatility: {patterns.get('volatility', 'unknown')}"
        
        decision = AgentDecision(
            action="market_prediction",
            confidence=confidence,
            reasoning=reasoning,
            data={
                "prediction": prediction,
                "patterns": patterns,
                "recommendation": self._generate_recommendation(prediction, confidence)
            },
            agent_type=self.agent_type.value
        )
        
        return decision
    
    async def _detect_patterns(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect patterns in market data using AI"""
        patterns = {}
        
        # Price trend analysis
        if "prices" in market_data:
            prices = market_data["prices"]
            if len(prices) >= 3:
                recent_trend = "bullish" if prices[-1] > prices[-3] else "bearish"
                patterns["trend"] = recent_trend
        
        # Volume analysis
        if "volume" in market_data:
            volume = market_data["volume"]
            avg_volume = sum(volume) / len(volume) if volume else 0
            patterns["volume_trend"] = "high" if volume[-1] > avg_volume * 1.2 else "normal"
        
        # Volatility calculation
        if "prices" in market_data:
            prices = market_data["prices"]
            if len(prices) >= 5:
                volatility = self._calculate_volatility(prices)
                patterns["volatility"] = "high" if volatility > 0.1 else "low"
        
        return patterns
    
    def _calculate_volatility(self, prices: List[float]) -> float:
        """Calculate price volatility"""
        if len(prices) < 2:
            return 0.0
        
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        avg_return = sum(returns) / len(returns)
        variance = sum([(r - avg_return) ** 2 for r in returns]) / len(returns)
        return variance ** 0.5
    
    async def _generate_prediction(self, patterns: Dict[str, Any], user_prefs: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Generate market prediction based on patterns and context"""
        prediction = {
            "direction": "neutral",
            "strength": 0.5,
            "timeframe": "1h",
            "key_levels": []
        }
        
        # Trend-based prediction
        if patterns.get("trend") == "bullish":
            prediction["direction"] = "up"
            prediction["strength"] = 0.7
        elif patterns.get("trend") == "bearish":
            prediction["direction"] = "down"
            prediction["strength"] = 0.7
        
        # Adjust for volatility
        if patterns.get("volatility") == "high":
            prediction["strength"] *= 1.2  # Higher confidence in trending markets with high volatility
        
        # Consider user preferences
        risk_tolerance = user_prefs.get("risk_tolerance", "medium")
        if risk_tolerance == "low" and prediction["strength"] < 0.8:
            prediction["direction"] = "neutral"
            prediction["strength"] = 0.5
        
        return prediction
    
    def _generate_recommendation(self, prediction: Dict[str, Any], confidence: float) -> str:
        """Generate actionable recommendation"""
        direction = prediction["direction"]
        strength = prediction["strength"]
        
        if confidence < 0.5:
            return "Insufficient data for reliable recommendation. Monitor market conditions."
        
        if direction == "up" and strength > 0.7:
            return f"Consider long position. Confidence: {confidence:.1%}"
        elif direction == "down" and strength > 0.7:
            return f"Consider short position or exit longs. Confidence: {confidence:.1%}"
        else:
            return f"Market neutral. Wait for clearer signals. Confidence: {confidence:.1%}"
    
    def _calculate_confidence(self, patterns: Dict[str, Any], context: AgentContext) -> float:
        """Calculate confidence based on patterns and historical performance"""
        base_confidence = 0.5
        
        # Adjust based on pattern strength
        if len(patterns) >= 3:
            base_confidence += 0.2
        
        # Historical performance adjustment
        success_rate = self.performance_metrics["success_rate"]
        base_confidence += (success_rate - 0.5) * 0.4
        
        # Context-based adjustment
        if context.history and len(context.history) > 5:
            base_confidence += 0.1  # More confident with more context
        
        return min(max(base_confidence, 0.1), 0.95)  # Clamp between 10% and 95%
    
    async def learn_from_feedback(self, learning_data: LearningData) -> bool:
        """Learn from market prediction feedback"""
        self.learning_history.append(learning_data)
        self.performance_metrics["learning_iterations"] += 1
        
        # Update pattern accuracy
        prediction = learning_data.output_data.get("prediction", {})
        actual_direction = learning_data.feedback
        predicted_direction = prediction.get("direction")
        
        if predicted_direction and actual_direction:
            accuracy_key = f"pattern_{predicted_direction}"
            if accuracy_key not in self.prediction_accuracy:
                self.prediction_accuracy[accuracy_key] = {"correct": 0, "total": 0}
            
            self.prediction_accuracy[accuracy_key]["total"] += 1
            if predicted_direction == actual_direction:
                self.prediction_accuracy[accuracy_key]["correct"] += 1
        
        # Adjust decision threshold based on recent performance
        if len(self.learning_history) >= 10:
            recent_success = sum(1 for data in self.learning_history[-10:] if data.success_metric > 0.7) / 10
            if recent_success < 0.4:
                self.decision_threshold = min(0.9, self.decision_threshold + 0.05)
            elif recent_success > 0.8:
                self.decision_threshold = max(0.5, self.decision_threshold - 0.02)
        
        return True


class DiscordModeratorAgent(BaseIntelligentAgent):
    """Intelligent agent for Discord moderation and user interaction"""
    
    def __init__(self):
        super().__init__(
            AgentType.DISCORD_MODERATOR,
            [AgentCapability.ANALYSIS, AgentCapability.DECISION_MAKING, AgentCapability.CONTEXT_AWARENESS]
        )
        self.user_behavior_patterns = {}
        self.moderation_rules = {}
    
    async def analyze(self, input_data: Dict[str, Any], context: AgentContext) -> AgentDecision:
        """Analyze Discord message and determine appropriate response"""
        message = input_data.get("message", "")
        user_id = input_data.get("user_id")
        channel_id = input_data.get("channel_id")
        
        # Analyze message content
        analysis = await self._analyze_message(message, user_id, context)
        
        # Determine action
        action = await self._determine_action(analysis, context)
        
        # Calculate confidence
        confidence = self._calculate_response_confidence(analysis, context)
        
        reasoning = f"Message analysis: {analysis.get('type', 'normal')}. " \
                   f"User behavior score: {analysis.get('user_score', 'unknown')}. " \
                   f"Context relevance: {analysis.get('relevance', 'unknown')}"
        
        decision = AgentDecision(
            action=action["type"],
            confidence=confidence,
            reasoning=reasoning,
            data={
                "response": action.get("response"),
                "moderation_action": action.get("moderation"),
                "analysis": analysis
            },
            agent_type=self.agent_type.value
        )
        
        return decision
    
    async def _analyze_message(self, message: str, user_id: str, context: AgentContext) -> Dict[str, Any]:
        """Analyze message content and user behavior"""
        analysis = {
            "type": "normal",
            "sentiment": "neutral", 
            "relevance": 0.5,
            "user_score": 0.5,
            "flags": []
        }
        
        message_lower = message.lower()
        
        # Content type detection
        if any(word in message_lower for word in ["price", "chart", "buy", "sell", "pump", "dump"]):
            analysis["type"] = "trading_discussion"
            analysis["relevance"] = 0.8
        elif any(word in message_lower for word in ["help", "question", "how", "what", "why"]):
            analysis["type"] = "help_request"
            analysis["relevance"] = 0.9
        elif any(word in message_lower for word in ["spam", "scam", "fake", "bot"]):
            analysis["type"] = "potential_spam"
            analysis["flags"].append("spam_keywords")
        
        # Sentiment analysis (basic)
        positive_words = ["good", "great", "awesome", "thanks", "helpful", "love"]
        negative_words = ["bad", "terrible", "hate", "stupid", "scam", "fake"]
        
        pos_count = sum(1 for word in positive_words if word in message_lower)
        neg_count = sum(1 for word in negative_words if word in message_lower)
        
        if pos_count > neg_count:
            analysis["sentiment"] = "positive"
        elif neg_count > pos_count:
            analysis["sentiment"] = "negative"
        
        # User behavior analysis
        if user_id:
            user_history = self.get_context_memory(f"user_{user_id}")
            if user_history:
                analysis["user_score"] = user_history.get("reputation_score", 0.5)
                if user_history.get("spam_count", 0) > 3:
                    analysis["flags"].append("frequent_spammer")
        
        return analysis
    
    async def _determine_action(self, analysis: Dict[str, Any], context: AgentContext) -> Dict[str, Any]:
        """Determine appropriate response action"""
        action = {
            "type": "respond",
            "response": None,
            "moderation": None
        }
        
        message_type = analysis["type"]
        flags = analysis["flags"]
        
        # Handle different message types
        if message_type == "help_request":
            action["response"] = await self._generate_helpful_response(analysis, context)
        elif message_type == "trading_discussion":
            action["response"] = await self._generate_trading_response(analysis, context)
        elif message_type == "potential_spam":
            if "frequent_spammer" in flags:
                action["moderation"] = "warn_user"
                action["response"] = "Please avoid posting spam content. This is your warning."
            else:
                action["response"] = "Please keep discussions relevant to the channel topic."
        
        # Default helpful response
        if not action["response"] and analysis["relevance"] > 0.7:
            action["response"] = await self._generate_contextual_response(analysis, context)
        
        return action
    
    async def _generate_helpful_response(self, analysis: Dict[str, Any], context: AgentContext) -> str:
        """Generate helpful response to user questions"""
        responses = [
            "I'd be happy to help! Can you provide more details about what you're looking for?",
            "Great question! Let me see what information I can provide.",
            "I'm here to assist. What specific aspect would you like to know more about?"
        ]
        return responses[len(context.history) % len(responses)]
    
    async def _generate_trading_response(self, analysis: Dict[str, Any], context: AgentContext) -> str:
        """Generate response to trading discussions"""
        if analysis["sentiment"] == "positive":
            return "Remember to always do your own research and never invest more than you can afford to lose!"
        elif analysis["sentiment"] == "negative":
            return "Market volatility is normal. Consider your long-term strategy and risk management."
        else:
            return "For trading questions, please check our resources channel or consult with qualified advisors."
    
    async def _generate_contextual_response(self, analysis: Dict[str, Any], context: AgentContext) -> str:
        """Generate contextual response based on analysis"""
        if analysis["sentiment"] == "positive":
            return "Thanks for the positive contribution to our community!"
        elif context.metadata.get("channel_type") == "general":
            return "Thanks for sharing! Feel free to ask if you have any questions."
        else:
            return None  # No response needed
    
    def _calculate_response_confidence(self, analysis: Dict[str, Any], context: AgentContext) -> float:
        """Calculate confidence in response decision"""
        base_confidence = 0.6
        
        # Higher confidence for clear message types
        if analysis["type"] in ["help_request", "trading_discussion"]:
            base_confidence += 0.2
        
        # Adjust for user history
        if analysis["user_score"] > 0.7:
            base_confidence += 0.1
        elif analysis["user_score"] < 0.3:
            base_confidence += 0.15  # More confident in moderation actions
        
        # Adjust for flags
        if analysis["flags"]:
            base_confidence += 0.1  # More confident when clear violations detected
        
        return min(max(base_confidence, 0.1), 0.95)
    
    async def learn_from_feedback(self, learning_data: LearningData) -> bool:
        """Learn from moderation feedback"""
        self.learning_history.append(learning_data)
        
        # Update user behavior patterns
        input_data = learning_data.input_data
        user_id = input_data.get("user_id")
        
        if user_id and learning_data.feedback:
            user_key = f"user_{user_id}"
            user_data = self.get_context_memory(user_key) or {"reputation_score": 0.5, "spam_count": 0}
            
            if learning_data.feedback == "helpful":
                user_data["reputation_score"] = min(1.0, user_data["reputation_score"] + 0.05)
            elif learning_data.feedback == "spam":
                user_data["spam_count"] += 1
                user_data["reputation_score"] = max(0.0, user_data["reputation_score"] - 0.1)
            
            self.update_context_memory(user_key, user_data)
        
        return True


class WorkflowOptimizerAgent(BaseIntelligentAgent):
    """Intelligent agent for optimizing n8n workflows and system performance"""
    
    def __init__(self):
        super().__init__(
            AgentType.WORKFLOW_OPTIMIZER,
            [AgentCapability.OPTIMIZATION, AgentCapability.ANALYSIS, AgentCapability.LEARNING]
        )
        self.workflow_performance = {}
        self.optimization_history = []
    
    async def analyze(self, input_data: Dict[str, Any], context: AgentContext) -> AgentDecision:
        """Analyze workflow performance and suggest optimizations"""
        workflow_data = input_data.get("workflow_data", {})
        performance_metrics = input_data.get("performance_metrics", {})
        
        # Analyze current performance
        analysis = await self._analyze_workflow_performance(workflow_data, performance_metrics)
        
        # Generate optimizations
        optimizations = await self._generate_optimizations(analysis, context)
        
        # Calculate confidence
        confidence = self._calculate_optimization_confidence(analysis, context)
        
        reasoning = f"Performance analysis: {analysis.get('bottlenecks', [])}. " \
                   f"Efficiency score: {analysis.get('efficiency_score', 'unknown')}. " \
                   f"Optimization potential: {analysis.get('optimization_potential', 'unknown')}"
        
        decision = AgentDecision(
            action="optimize_workflow",
            confidence=confidence,
            reasoning=reasoning,
            data={
                "optimizations": optimizations,
                "analysis": analysis,
                "priority_order": self._prioritize_optimizations(optimizations)
            },
            agent_type=self.agent_type.value
        )
        
        return decision
    
    async def _analyze_workflow_performance(self, workflow_data: Dict[str, Any], metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze workflow performance metrics"""
        analysis = {
            "efficiency_score": 0.5,
            "bottlenecks": [],
            "optimization_potential": "medium",
            "resource_usage": "normal"
        }
        
        # Analyze execution time
        avg_execution_time = metrics.get("avg_execution_time", 0)
        if avg_execution_time > 10:  # seconds
            analysis["bottlenecks"].append("slow_execution")
            analysis["efficiency_score"] -= 0.2
        
        # Analyze error rate
        error_rate = metrics.get("error_rate", 0)
        if error_rate > 0.05:  # 5%
            analysis["bottlenecks"].append("high_error_rate")
            analysis["efficiency_score"] -= 0.15
        
        # Analyze resource usage
        cpu_usage = metrics.get("cpu_usage", 0)
        memory_usage = metrics.get("memory_usage", 0)
        
        if cpu_usage > 0.8 or memory_usage > 0.8:
            analysis["resource_usage"] = "high"
            analysis["bottlenecks"].append("resource_intensive")
        
        # Analyze workflow complexity
        node_count = len(workflow_data.get("nodes", []))
        if node_count > 20:
            analysis["bottlenecks"].append("high_complexity")
        
        # Calculate overall efficiency
        if analysis["efficiency_score"] < 0.3:
            analysis["optimization_potential"] = "high"
        elif analysis["efficiency_score"] > 0.7:
            analysis["optimization_potential"] = "low"
        
        return analysis
    
    async def _generate_optimizations(self, analysis: Dict[str, Any], context: AgentContext) -> List[Dict[str, Any]]:
        """Generate specific optimization recommendations"""
        optimizations = []
        
        for bottleneck in analysis["bottlenecks"]:
            if bottleneck == "slow_execution":
                optimizations.append({
                    "type": "performance",
                    "action": "add_caching",
                    "description": "Add caching layers to reduce API call frequency",
                    "impact": "high",
                    "difficulty": "medium"
                })
                optimizations.append({
                    "type": "performance",
                    "action": "parallel_processing",
                    "description": "Enable parallel processing for independent operations",
                    "impact": "high",
                    "difficulty": "low"
                })
            
            elif bottleneck == "high_error_rate":
                optimizations.append({
                    "type": "reliability",
                    "action": "add_retry_logic",
                    "description": "Add retry mechanisms with exponential backoff",
                    "impact": "medium",
                    "difficulty": "low"
                })
                optimizations.append({
                    "type": "reliability", 
                    "action": "improve_error_handling",
                    "description": "Add comprehensive error handling and logging",
                    "impact": "medium",
                    "difficulty": "medium"
                })
            
            elif bottleneck == "resource_intensive":
                optimizations.append({
                    "type": "efficiency",
                    "action": "optimize_queries",
                    "description": "Optimize database queries and API calls",
                    "impact": "high",
                    "difficulty": "high"
                })
                optimizations.append({
                    "type": "efficiency",
                    "action": "implement_batching",
                    "description": "Batch similar operations to reduce overhead",
                    "impact": "medium",
                    "difficulty": "medium"
                })
            
            elif bottleneck == "high_complexity":
                optimizations.append({
                    "type": "maintainability",
                    "action": "refactor_workflow",
                    "description": "Break down complex workflow into smaller, manageable pieces",
                    "impact": "high",
                    "difficulty": "high"
                })
        
        return optimizations
    
    def _prioritize_optimizations(self, optimizations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize optimizations by impact and difficulty"""
        impact_scores = {"high": 3, "medium": 2, "low": 1}
        difficulty_scores = {"low": 1, "medium": 2, "high": 3}
        
        for opt in optimizations:
            impact = impact_scores.get(opt.get("impact", "medium"), 2)
            difficulty = difficulty_scores.get(opt.get("difficulty", "medium"), 2)
            opt["priority_score"] = impact / difficulty
        
        return sorted(optimizations, key=lambda x: x["priority_score"], reverse=True)
    
    def _calculate_optimization_confidence(self, analysis: Dict[str, Any], context: AgentContext) -> float:
        """Calculate confidence in optimization recommendations"""
        base_confidence = 0.6
        
        # Higher confidence with clear bottlenecks
        bottleneck_count = len(analysis["bottlenecks"])
        if bottleneck_count >= 2:
            base_confidence += 0.2
        elif bottleneck_count == 0:
            base_confidence -= 0.2
        
        # Adjust for optimization potential
        potential = analysis["optimization_potential"]
        if potential == "high":
            base_confidence += 0.15
        elif potential == "low":
            base_confidence -= 0.1
        
        # Historical success adjustment
        success_rate = self.performance_metrics["success_rate"]
        base_confidence += (success_rate - 0.5) * 0.3
        
        return min(max(base_confidence, 0.1), 0.95)
    
    async def learn_from_feedback(self, learning_data: LearningData) -> bool:
        """Learn from optimization results"""
        self.learning_history.append(learning_data)
        self.optimization_history.append(learning_data)
        
        # Track optimization effectiveness
        optimization_data = learning_data.output_data.get("optimizations", [])
        success_metric = learning_data.success_metric
        
        for opt in optimization_data:
            opt_type = opt.get("type")
            if opt_type not in self.workflow_performance:
                self.workflow_performance[opt_type] = {"attempts": 0, "successes": 0}
            
            self.workflow_performance[opt_type]["attempts"] += 1
            if success_metric > 0.7:
                self.workflow_performance[opt_type]["successes"] += 1
        
        return True


class AgentOrchestrator:
    """Central orchestrator for managing multiple intelligent agents"""
    
    def __init__(self):
        self.agents: Dict[AgentType, BaseIntelligentAgent] = {}
        self.agent_routing_rules = {}
        self.collaboration_patterns = {}
        self.register_default_agents()
    
    def register_default_agents(self):
        """Register default intelligent agents"""
        self.agents[AgentType.MARKET_ANALYZER] = MarketAnalyzerAgent()
        self.agents[AgentType.DISCORD_MODERATOR] = DiscordModeratorAgent() 
        self.agents[AgentType.WORKFLOW_OPTIMIZER] = WorkflowOptimizerAgent()
    
    def register_agent(self, agent_type: AgentType, agent: BaseIntelligentAgent):
        """Register a new agent"""
        self.agents[agent_type] = agent
        logger.info(f"Registered agent: {agent_type.value}")
    
    async def route_request(self, request_type: str, input_data: Dict[str, Any], context: AgentContext) -> AgentDecision:
        """Route request to appropriate agent"""
        agent_type = self._determine_agent(request_type, input_data)
        
        if agent_type not in self.agents:
            return AgentDecision(
                action="no_agent_available",
                confidence=0.0,
                reasoning=f"No agent available for request type: {request_type}",
                data={"error": f"Unknown request type: {request_type}"},
                agent_type="orchestrator"
            )
        
        agent = self.agents[agent_type]
        decision = await agent.analyze(input_data, context)
        
        # Update agent performance
        agent.update_performance_metrics(decision, True)  # Assume success for now
        
        return decision
    
    def _determine_agent(self, request_type: str, input_data: Dict[str, Any]) -> AgentType:
        """Determine which agent should handle the request"""
        request_type_lower = request_type.lower()
        
        if "market" in request_type_lower or "trading" in request_type_lower or "price" in request_type_lower:
            return AgentType.MARKET_ANALYZER
        elif "discord" in request_type_lower or "message" in request_type_lower or "moderation" in request_type_lower:
            return AgentType.DISCORD_MODERATOR
        elif "workflow" in request_type_lower or "optimize" in request_type_lower or "performance" in request_type_lower:
            return AgentType.WORKFLOW_OPTIMIZER
        else:
            # Default to Discord moderator for general requests
            return AgentType.DISCORD_MODERATOR
    
    async def collaborative_analysis(self, request_type: str, input_data: Dict[str, Any], context: AgentContext, agent_types: List[AgentType]) -> List[AgentDecision]:
        """Get analysis from multiple agents for collaborative decision-making"""
        decisions = []
        
        for agent_type in agent_types:
            if agent_type in self.agents:
                agent = self.agents[agent_type]
                decision = await agent.analyze(input_data, context)
                decisions.append(decision)
        
        return decisions
    
    def get_agent_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all registered agents"""
        status = {}
        
        for agent_type, agent in self.agents.items():
            status[agent_type.value] = agent.get_performance_report()
        
        return status
    
    async def provide_feedback(self, agent_type: AgentType, learning_data: LearningData) -> bool:
        """Provide feedback to specific agent for learning"""
        if agent_type in self.agents:
            agent = self.agents[agent_type]
            return await agent.learn_from_feedback(learning_data)
        return False


# Global agent orchestrator instance
agent_orchestrator = AgentOrchestrator()

# Convenience functions for easy integration
async def analyze_with_intelligence(request_type: str, input_data: Dict[str, Any], context: Optional[AgentContext] = None) -> AgentDecision:
    """Analyze request using intelligent agents"""
    if context is None:
        context = AgentContext()
    
    return await agent_orchestrator.route_request(request_type, input_data, context)

async def collaborative_intelligence(request_type: str, input_data: Dict[str, Any], agent_types: List[AgentType], context: Optional[AgentContext] = None) -> List[AgentDecision]:
    """Get collaborative analysis from multiple agents"""
    if context is None:
        context = AgentContext()
    
    return await agent_orchestrator.collaborative_analysis(request_type, input_data, context, agent_types)

def get_agent_performance() -> Dict[str, Dict[str, Any]]:
    """Get performance report for all agents"""
    return agent_orchestrator.get_agent_status()

async def train_agent(agent_type: AgentType, input_data: Dict[str, Any], output_data: Dict[str, Any], success_metric: float, feedback: str) -> bool:
    """Train specific agent with feedback data"""
    learning_data = LearningData(
        input_data=input_data,
        output_data=output_data,
        success_metric=success_metric,
        feedback=feedback,
        context=AgentContext()
    )
    
    return await agent_orchestrator.provide_feedback(agent_type, learning_data)