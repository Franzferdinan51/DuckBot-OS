#!/usr/bin/env python3
"""
N8N Agent Helper Script
Called by n8n nodes to interact with DuckBot intelligent agents
"""

import sys
import json
import asyncio
import logging

# Suppress logging for clean output
logging.getLogger().setLevel(logging.ERROR)

async def call_agent(request_data):
    """Call intelligent agent and return result"""
    try:
        # Import DuckBot agents
        from duckbot.intelligent_agents import analyze_with_intelligence, AgentContext, AgentType
        
        agent_type = request_data.get("agent_type", "general")
        input_data = request_data.get("input_data", {})
        context_data = request_data.get("context", {})
        
        # Create agent context
        context = AgentContext(
            user_id=context_data.get("user_id"),
            timestamp=context_data.get("timestamp"),
            environment=input_data,
            metadata=context_data
        )
        
        # Analyze with intelligent agent
        decision = await analyze_with_intelligence(agent_type, input_data, context)
        
        # Return result
        return {
            "success": True,
            "confidence": decision.confidence,
            "reasoning": decision.reasoning,
            "action": decision.action,
            "data": decision.data,
            "agent_type": decision.agent_type
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "confidence": 0.0
        }

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "No request data provided"}))
        sys.exit(1)
    
    try:
        request_data = json.loads(sys.argv[1])
        result = asyncio.run(call_agent(request_data))
        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()