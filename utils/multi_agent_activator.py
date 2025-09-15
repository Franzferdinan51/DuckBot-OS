#!/usr/bin/env python3
"""
DuckBot Multi-Agent System Activator
Activates and manages the complete sub-agent system for enhanced AI capabilities
"""

import asyncio
import sys
import os
from pathlib import Path
import logging
from typing import Dict, Any, List

# Add DuckBot path
sys.path.append(str(Path(__file__).parent))

from duckbot.agents.intelligent_agents import (
    AgentOrchestrator, AgentType, AgentContext, AgentCapability,
    MarketAnalyzerAgent, DiscordModeratorAgent, WorkflowOptimizerAgent,
    MiningManagerAgent, BaseIntelligentAgent
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiAgentSystem:
    """Complete multi-agent system management"""

    def __init__(self):
        self.orchestrator = AgentOrchestrator()
        self.active_agents = {}
        self.task_queue = asyncio.Queue()
        self.collaboration_mode = True
        self.current_session_id = None

    async def initialize(self):
        """Initialize all agents and coordination systems"""
        logger.info("🤖 Initializing DuckBot Multi-Agent System...")

        # Initialize core orchestrator
        await self._setup_orchestrator()

        # Activate all available agents
        await self._activate_agents()

        # Setup coordination systems
        await self._setup_coordination()

        logger.info("✅ Multi-Agent System Activated Successfully!")
        return self

    async def _setup_orchestrator(self):
        """Setup the main orchestrator"""
        # Ensure all agents are registered
        self.orchestrator.register_default_agents()

        # Add additional specialized agents (extend existing ones with new capabilities)
        self._create_enhanced_agents()

    async def _activate_agents(self):
        """Activate all registered agents"""
        for agent_type, agent in self.orchestrator.agents.items():
            try:
                # Initialize agent capabilities
                await self._initialize_agent_capabilities(agent)
                self.active_agents[agent_type] = agent
                logger.info(f"🤖 Agent Activated: {agent_type.value}")
            except Exception as e:
                logger.error(f"❌ Failed to activate {agent_type.value}: {e}")

    async def _initialize_agent_capabilities(self, agent):
        """Initialize specific agent capabilities"""
        # Set up learning systems
        agent.learning_history = []
        agent.context_memory = {}

        # Configure agent-specific settings
        if hasattr(agent, 'setup_capabilities'):
            await agent.setup_capabilities()

    async def _setup_coordination(self):
        """Setup coordination and collaboration systems"""
        # Setup collaboration patterns
        self.orchestrator.collaboration_patterns = {
            'parallel_analysis': {
                'agents': [AgentType.MARKET_ANALYZER, AgentType.WORKFLOW_OPTIMIZER,
                          AgentType.DISCORD_MODERATOR],
                'coordination': 'parallel'
            },
            'sequential_workflow': {
                'agents': [AgentType.WORKFLOW_OPTIMIZER, AgentType.MARKET_ANALYZER,
                          AgentType.DISCORD_MODERATOR],
                'coordination': 'sequential'
            },
            'consensus_decision': {
                'agents': [AgentType.MARKET_ANALYZER, AgentType.MINING_MANAGER,
                          AgentType.WORKFLOW_OPTIMIZER],
                'coordination': 'consensus'
            }
        }

        # Setup routing rules
        self.orchestrator.agent_routing_rules = {
            'market_analysis': AgentType.MARKET_ANALYZER,
            'workflow_optimization': AgentType.WORKFLOW_OPTIMIZER,
            'user_interaction': AgentType.DISCORD_MODERATOR,  # Use discord mod for user interaction
            'mining_operations': AgentType.MINING_MANAGER,
            'system_analysis': AgentType.MARKET_ANALYZER  # Use market analyzer for general analysis
        }

    def _create_enhanced_agents(self):
        """Create enhanced versions of existing agents with additional capabilities"""
        # Enhance existing agents with additional capabilities
        for agent_type, agent in self.orchestrator.agents.items():
            # Add new capabilities to existing agents
            agent.capabilities.extend([
                AgentCapability.LEARNING,
                AgentCapability.ADAPTATION,
                AgentCapability.CONTEXT_AWARENESS
            ])
            logger.info(f"🔧 Enhanced {agent_type.value} with additional capabilities")

    async def process_request(self, request_type: str, input_data: Dict[str, Any],
                             context: AgentContext = None) -> Dict[str, Any]:
        """Process a request using the multi-agent system"""
        if context is None:
            context = AgentContext(
                session_id=self.current_session_id,
                environment={'multi_agent_active': True}
            )

        # Determine best approach for this request
        approach = await self._determine_approach(request_type, input_data)

        if approach == 'collaborative':
            return await self._collaborative_analysis(request_type, input_data, context)
        elif approach == 'specialized':
            return await self._specialized_analysis(request_type, input_data, context)
        else:
            return await self._orchestrated_analysis(request_type, input_data, context)

    async def _determine_approach(self, request_type: str, input_data: Dict[str, Any]) -> str:
        """Determine if collaborative, specialized, or orchestrated approach is best"""
        # Simple heuristics - can be enhanced with learning
        if request_type in ['complex_analysis', 'strategic_planning']:
            return 'collaborative'
        elif request_type in self.orchestrator.agent_routing_rules:
            return 'specialized'
        else:
            return 'orchestrated'

    async def _collaborative_analysis(self, request_type: str, input_data: Dict[str, Any],
                                   context: AgentContext) -> Dict[str, Any]:
        """Collaborative analysis with multiple agents"""
        logger.info(f"🤝 Starting collaborative analysis for: {request_type}")

        # Get agents for this collaboration
        pattern = self.orchestrator.collaboration_patterns.get('parallel_analysis', {})
        agent_types = pattern.get('agents', list(self.active_agents.keys())[:3])

        # Run parallel analysis
        tasks = []
        for agent_type in agent_types:
            if agent_type in self.active_agents:
                agent = self.active_agents[agent_type]
                task = asyncio.create_task(agent.analyze(input_data, context))
                tasks.append((agent_type, task))

        # Collect results
        results = {}
        for agent_type, task in tasks:
            try:
                decision = await task
                results[agent_type.value] = decision
                logger.info(f"✅ {agent_type.value} analysis completed")
            except Exception as e:
                logger.error(f"❌ {agent_type.value} analysis failed: {e}")

        return {
            'approach': 'collaborative',
            'results': results,
            'consensus': await self._build_consensus(results),
            'coordinated_by': 'multi-agent_system'
        }

    async def _specialized_analysis(self, request_type: str, input_data: Dict[str, Any],
                                  context: AgentContext) -> Dict[str, Any]:
        """Specialized analysis with single best agent"""
        agent_type = self.orchestrator.agent_routing_rules.get(request_type)

        if agent_type and agent_type in self.active_agents:
            agent = self.active_agents[agent_type]
            result = await agent.analyze(input_data, context)

            return {
                'approach': 'specialized',
                'agent': agent_type.value,
                'result': result,
                'coordinated_by': 'multi-agent_system'
            }

        # Fallback to orchestrated
        return await self._orchestrated_analysis(request_type, input_data, context)

    async def _orchestrated_analysis(self, request_type: str, input_data: Dict[str, Any],
                                   context: AgentContext) -> Dict[str, Any]:
        """Orchestrated analysis with agent selection"""
        # Let orchestrator select best agent(s)
        agent_types = list(self.active_agents.keys())

        results = []
        for agent_type in agent_types:
            agent = self.active_agents[agent_type]
            try:
                decision = await agent.analyze(input_data, context)
                results.append(decision)
            except Exception as e:
                logger.warning(f"⚠️ Agent {agent_type.value} failed: {e}")

        return {
            'approach': 'orchestrated',
            'results': results,
            'best_result': await self._select_best_result(results),
            'coordinated_by': 'multi-agent_system'
        }

    async def _build_consensus(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Build consensus from multiple agent results"""
        # Simple consensus building - can be enhanced
        if not results:
            return {'consensus_strength': 0, 'decision': 'no_consensus'}

        # Analyze agreement between agents
        decisions = [result.get('action', '') for result in results.values()]
        confidence_scores = [result.get('confidence', 0) for result in results.values()]

        # Calculate consensus strength
        unique_decisions = set(decisions)
        consensus_strength = len(unique_decisions) / len(decisions) if decisions else 0

        return {
            'consensus_strength': consensus_strength,
            'agreement_level': 'high' if consensus_strength > 0.7 else 'medium' if consensus_strength > 0.4 else 'low',
            'participating_agents': list(results.keys()),
            'average_confidence': sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        }

    async def _select_best_result(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Select the best result from multiple agents"""
        if not results:
            return {}

        # Sort by confidence and select best
        sorted_results = sorted(results, key=lambda x: x.get('confidence', 0), reverse=True)
        return sorted_results[0]

    def get_system_status(self) -> Dict[str, Any]:
        """Get current multi-agent system status"""
        return {
            'system_active': True,
            'total_agents': len(self.active_agents),
            'active_agents': list(self.active_agents.keys()),
            'collaboration_mode': self.collaboration_mode,
            'session_id': self.current_session_id,
            'orchestrator_status': 'active'
        }

    async def shutdown(self):
        """Shutdown the multi-agent system"""
        logger.info("🔄 Shutting down Multi-Agent System...")

        # Graceful shutdown of all agents
        for agent_type, agent in self.active_agents.items():
            if hasattr(agent, 'cleanup'):
                try:
                    await agent.cleanup()
                except Exception as e:
                    logger.warning(f"⚠️ Failed to cleanup {agent_type.value}: {e}")

        self.active_agents.clear()
        logger.info("✅ Multi-Agent System Shutdown Complete")

# Global multi-agent system instance
multi_agent_system = None

async def get_multi_agent_system() -> MultiAgentSystem:
    """Get or create the global multi-agent system instance"""
    global multi_agent_system
    if multi_agent_system is None:
        multi_agent_system = MultiAgentSystem()
        await multi_agent_system.initialize()
    return multi_agent_system

async def activate_multi_agent_system():
    """Activate the multi-agent system for use"""
    system = await get_multi_agent_system()
    logger.info("🚀 Multi-Agent System Ready for Operation!")
    return system