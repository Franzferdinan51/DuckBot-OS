#!/usr/bin/env python3
"""
Multi-Agent System Interface for Active Use
Simple interface to leverage DuckBot's multi-agent capabilities
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from multi_agent_activator import get_multi_agent_system
from duckbot.agents.intelligent_agents import AgentContext, AgentType

class MultiAgentInterface:
    """User-friendly interface for multi-agent system"""

    def __init__(self):
        self.system = None
        self.session_id = None

    async def initialize(self):
        """Initialize the multi-agent system"""
        self.system = await get_multi_agent_system()
        self.session_id = f"session_{asyncio.get_event_loop().time()}"
        print("Multi-Agent System Ready!")
        return self

    async def analyze_with_agents(self, query: str, analysis_type: str = "general") -> Dict[str, Any]:
        """
        Analyze a query using multiple agents

        Args:
            query: The question or task to analyze
            analysis_type: Type of analysis (market, workflow, user_interaction, system_analysis, complex)

        Returns:
            Results from agent analysis
        """
        if not self.system:
            await self.initialize()

        # Determine request type based on analysis type
        request_type_mapping = {
            "market": "market_analysis",
            "workflow": "workflow_optimization",
            "user": "user_interaction",
            "system": "system_analysis",
            "complex": "complex_analysis",
            "general": "general_analysis"
        }

        request_type = request_type_mapping.get(analysis_type, "general_analysis")

        # Prepare input data
        input_data = {
            "query": query,
            "analysis_type": analysis_type,
            "complexity": "high" if analysis_type == "complex" else "medium"
        }

        # Create context
        context = AgentContext(
            session_id=self.session_id,
            environment={"interface": "multi_agent_interface"}
        )

        # Process with multi-agent system
        result = await self.system.process_request(request_type, input_data, context)

        return result

    async def get_agent_insights(self, query: str) -> Dict[str, Any]:
        """
        Get insights from different specialized agents

        Args:
            query: The question or task to analyze

        Returns:
            Structured insights from different agent perspectives
        """
        if not self.system:
            await self.initialize()

        # Get collaborative analysis
        result = await self.analyze_with_agents(query, "complex")

        # Structure the insights
        insights = {
            "query": query,
            "approach": result.get("approach", "unknown"),
            "agent_count": len(result.get("results", {})),
            "insights_by_agent": {},
            "consensus": result.get("consensus", {}),
            "coordinated_by": result.get("coordinated_by", "multi_agent_system")
        }

        # Extract insights from each agent
        if "results" in result:
            for agent_name, agent_result in result["results"].items():
                insights["insights_by_agent"][agent_name] = {
                    "action": agent_result.get("action", ""),
                    "confidence": agent_result.get("confidence", 0),
                    "reasoning": agent_result.get("reasoning", ""),
                    "data": agent_result.get("data", {})
                }

        return insights

    async def collaborative_decision(self, problem: str) -> Dict[str, Any]:
        """
        Make collaborative decisions on complex problems

        Args:
            problem: Complex problem requiring multiple perspectives

        Returns:
            Collaborative decision with agent consensus
        """
        if not self.system:
            await self.initialize()

        # Format problem for decision analysis
        problem_data = {
            "problem_statement": problem,
            "decision_type": "strategic",
            "complexity_level": "high",
            "require_consensus": True
        }

        context = AgentContext(
            session_id=self.session_id,
            environment={"mode": "decision_making"}
        )

        # Use consensus decision approach
        result = await self.system.process_request("strategic_planning", problem_data, context)

        return {
            "problem": problem,
            "decision_approach": "collaborative_consensus",
            "agent_participants": result.get("consensus", {}).get("participating_agents", []),
            "consensus_strength": result.get("consensus", {}).get("consensus_strength", 0),
            "agreement_level": result.get("consensus", {}).get("agreement_level", "low"),
            "recommended_action": result.get("best_result", {}).get("action", ""),
            "confidence": result.get("best_result", {}).get("confidence", 0),
            "reasoning": result.get("best_result", {}).get("reasoning", "")
        }

    def get_system_status(self) -> Dict[str, Any]:
        """Get current multi-agent system status"""
        if self.system:
            return self.system.get_system_status()
        return {"status": "not_initialized"}

    def list_active_agents(self) -> List[str]:
        """List all currently active agents"""
        if self.system:
            return [agent_type.value for agent_type in self.system.active_agents.keys()]
        return []

# Global instance
multi_agent_interface = None

async def get_multi_agent_interface() -> MultiAgentInterface:
    """Get or create the global multi-agent interface"""
    global multi_agent_interface
    if multi_agent_interface is None:
        multi_agent_interface = MultiAgentInterface()
        await multi_agent_interface.initialize()
    return multi_agent_interface

# Convenience functions for direct use
async def analyze_with_agents(query: str, analysis_type: str = "general") -> Dict[str, Any]:
    """Quick analysis with multi-agents"""
    interface = await get_multi_agent_interface()
    return await interface.analyze_with_agents(query, analysis_type)

async def get_agent_insights(query: str) -> Dict[str, Any]:
    """Quick insights from multiple agents"""
    interface = await get_multi_agent_interface()
    return await interface.get_agent_insights(query)

async def collaborative_decision(problem: str) -> Dict[str, Any]:
    """Quick collaborative decision making"""
    interface = await get_multi_agent_interface()
    return await interface.collaborative_decision(problem)

# Example usage
async def demo_multi_agents():
    """Demonstrate multi-agent capabilities"""
    print("DuckBot Multi-Agent System Demo")
    print("=" * 50)

    # Test analysis
    print("\n1. Multi-Agent Analysis:")
    analysis = await analyze_with_agents(
        "What are the best strategies for optimizing AI system performance?",
        "system"
    )
    print(f"   Approach: {analysis['approach']}")
    print(f"   Coordinated by: {analysis['coordinated_by']}")

    # Test insights
    print("\n2. Agent Insights:")
    insights = await get_agent_insights("How to improve user engagement in AI systems?")
    print(f"   Participating agents: {insights['agent_count']}")
    print(f"   Consensus strength: {insights['consensus'].get('consensus_strength', 0):.2f}")

    # Test decision making
    print("\n3. Collaborative Decision:")
    decision = await collaborative_decision(
        "Should we invest more in cloud infrastructure or edge computing for our AI services?"
    )
    print(f"   Agreement level: {decision['agreement_level']}")
    print(f"   Recommended action: {decision['recommended_action']}")

    print("\nMulti-Agent Demo Complete!")

if __name__ == "__main__":
    asyncio.run(demo_multi_agents())