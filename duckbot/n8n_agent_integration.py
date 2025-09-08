"""
DuckBot n8n + Intelligent Agent Integration
Hybrid workflow system combining n8n automation with AI agent intelligence
"""

import json
import time
import asyncio
import logging
import requests
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import subprocess
import tempfile

logger = logging.getLogger(__name__)

class N8nAgentIntegration:
    """Integration layer between n8n workflows and intelligent agents"""
    
    def __init__(self, n8n_url: str = "http://localhost:5678"):
        self.n8n_url = n8n_url
        self.agent_nodes = {}
        self.workflow_enhancements = {}
        self.active_workflows = {}
        
        # Try to import intelligent agents
        try:
            from duckbot.intelligent_agents import (
                analyze_with_intelligence, AgentType, AgentContext,
                agent_orchestrator
            )
            self.agents_available = True
            self.agent_orchestrator = agent_orchestrator
            self.analyze_with_intelligence = analyze_with_intelligence
            self.AgentType = AgentType
            self.AgentContext = AgentContext
        except ImportError:
            self.agents_available = False
            logger.warning("Intelligent agents not available for n8n integration")
    
    def create_agent_enhanced_workflow(self, workflow_name: str, workflow_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create n8n workflow with AI agent enhancements"""
        
        base_workflow = {
            "name": workflow_name,
            "nodes": [],
            "connections": {},
            "active": True,
            "settings": {
                "timezone": "UTC",
                "saveManualExecutions": True,
                "callerPolicy": "workflowsFromSameOwner",
                "executionTimeout": 300
            },
            "staticData": {},
            "meta": {
                "instanceId": "duckbot-enhanced",
                "enhanced_with_agents": True,
                "agent_types": []
            }
        }
        
        # Add agent-enhanced nodes based on config
        node_counter = 1
        
        for step in workflow_config.get("steps", []):
            step_type = step.get("type")
            
            if step_type == "ai_agent":
                node = self._create_ai_agent_node(step, node_counter)
                base_workflow["nodes"].append(node)
                base_workflow["meta"]["agent_types"].append(step.get("agent_type", "general"))
                
            elif step_type == "data_transform":
                node = self._create_data_transform_node(step, node_counter)
                base_workflow["nodes"].append(node)
                
            elif step_type == "condition":
                node = self._create_intelligent_condition_node(step, node_counter)
                base_workflow["nodes"].append(node)
                
            elif step_type == "trigger":
                node = self._create_enhanced_trigger_node(step, node_counter)
                base_workflow["nodes"].append(node)
                
            elif step_type == "action":
                node = self._create_action_node(step, node_counter)
                base_workflow["nodes"].append(node)
            
            node_counter += 1
        
        # Create connections between nodes
        self._create_node_connections(base_workflow, workflow_config)
        
        return base_workflow
    
    def _create_ai_agent_node(self, config: Dict[str, Any], node_id: int) -> Dict[str, Any]:
        """Create n8n function node with AI agent integration"""
        
        agent_type = config.get("agent_type", "general")
        confidence_threshold = config.get("confidence_threshold", 0.7)
        
        # Generate function code that calls our AI agents
        function_code = f'''
// DuckBot AI Agent Integration Node
// Agent Type: {agent_type}
// Confidence Threshold: {confidence_threshold}

const {{ spawn }} = require('child_process');
const path = require('path');

// Input data from n8n
const inputData = items[0].json;

// Prepare agent analysis request
const agentRequest = {{
    agent_type: "{agent_type}",
    input_data: inputData,
    confidence_threshold: {confidence_threshold},
    context: {{
        workflow_name: this.getWorkflow().name,
        node_name: "{config.get('name', f'AI Agent {node_id}')}",
        timestamp: Date.now()
    }}
}};

// Call Python agent analysis script
const pythonScript = path.join(__dirname, '..', 'call_agent.py');
const pythonProcess = spawn('python', [pythonScript, JSON.stringify(agentRequest)]);

let result = '';
pythonProcess.stdout.on('data', (data) => {{
    result += data.toString();
}});

return new Promise((resolve, reject) => {{
    pythonProcess.on('close', (code) => {{
        if (code === 0) {{
            try {{
                const agentResult = JSON.parse(result);
                
                if (agentResult.success && agentResult.confidence >= {confidence_threshold}) {{
                    // Agent provided high-confidence result
                    resolve([{{
                        json: {{
                            ...inputData,
                            agent_analysis: agentResult,
                            enhanced_by_agent: true,
                            agent_type: "{agent_type}",
                            confidence: agentResult.confidence,
                            reasoning: agentResult.reasoning
                        }}
                    }}]);
                }} else {{
                    // Low confidence or failed analysis
                    resolve([{{
                        json: {{
                            ...inputData,
                            agent_analysis: agentResult,
                            enhanced_by_agent: false,
                            agent_type: "{agent_type}",
                            confidence: agentResult.confidence || 0,
                            error: agentResult.error || "Low confidence analysis"
                        }}
                    }}]);
                }}
            }} catch (e) {{
                reject(new Error(`Agent analysis failed: ${{e.message}}`));
            }}
        }} else {{
            reject(new Error(`Agent process exited with code ${{code}}`));
        }}
    }});
    
    pythonProcess.on('error', (error) => {{
        reject(new Error(`Failed to start agent process: ${{error.message}}`));
    }});
}});
        '''.strip()
        
        node = {
            "id": f"agent-{node_id}",
            "name": config.get("name", f"AI Agent {node_id}"),
            "type": "n8n-nodes-base.function",
            "typeVersion": 1,
            "position": config.get("position", [200 * node_id, 200]),
            "parameters": {
                "functionCode": function_code,
                "language": "javascript"
            },
            "credentials": {},
            "disabled": False,
            "notes": f"Enhanced with {agent_type} intelligent agent"
        }
        
        return node
    
    def _create_intelligent_condition_node(self, config: Dict[str, Any], node_id: int) -> Dict[str, Any]:
        """Create intelligent condition node that can learn from patterns"""
        
        condition_logic = config.get("condition", "confidence > 0.7")
        
        # Enhanced condition that considers agent recommendations
        condition_code = f'''
// Intelligent Condition Node with Agent Context
const inputData = items[0].json;

// Check if we have agent analysis
const hasAgentAnalysis = inputData.agent_analysis && inputData.enhanced_by_agent;
let conditionResult = false;

if (hasAgentAnalysis) {{
    // Use agent confidence and reasoning for decision
    const confidence = inputData.agent_analysis.confidence || 0;
    const reasoning = inputData.agent_analysis.reasoning || "";
    
    // Enhanced condition: {condition_logic}
    conditionResult = {condition_logic.replace("confidence", "confidence")};
    
    // Additional intelligent factors
    if (inputData.agent_analysis.action === "high_priority") {{
        conditionResult = true;
    }}
    
    if (reasoning.includes("urgent") || reasoning.includes("critical")) {{
        conditionResult = true;
    }}
}} else {{
    // Fallback to basic condition
    const confidence = inputData.confidence || 0.5;
    conditionResult = {condition_logic.replace("confidence", "confidence")};
}}

return [{{
    json: {{
        ...inputData,
        condition_result: conditionResult,
        condition_logic: "{condition_logic}",
        intelligent_decision: hasAgentAnalysis
    }}
}}];
        '''.strip()
        
        node = {
            "id": f"condition-{node_id}",
            "name": config.get("name", f"Intelligent Condition {node_id}"),
            "type": "n8n-nodes-base.function",
            "typeVersion": 1,
            "position": config.get("position", [200 * node_id, 200]),
            "parameters": {
                "functionCode": condition_code,
                "language": "javascript"
            },
            "credentials": {},
            "disabled": False,
            "notes": "Intelligent condition with agent context awareness"
        }
        
        return node
    
    def _create_enhanced_trigger_node(self, config: Dict[str, Any], node_id: int) -> Dict[str, Any]:
        """Create enhanced trigger node with intelligent filtering"""
        
        trigger_type = config.get("trigger_type", "webhook")
        
        if trigger_type == "webhook":
            node = {
                "id": f"trigger-{node_id}",
                "name": config.get("name", f"Enhanced Webhook {node_id}"),
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 1,
                "position": config.get("position", [200 * node_id, 200]),
                "parameters": {
                    "httpMethod": config.get("method", "POST"),
                    "path": config.get("path", f"enhanced-webhook-{node_id}"),
                    "responseMode": "responseNode",
                    "options": {
                        "rawBody": True,
                        "allowedOrigins": "http://localhost:8787,https://duckbot-ai.local"
                    }
                },
                "webhookId": f"enhanced-{node_id}",
                "credentials": {},
                "disabled": False,
                "notes": "Enhanced webhook with intelligent filtering"
            }
        
        elif trigger_type == "schedule":
            node = {
                "id": f"trigger-{node_id}",
                "name": config.get("name", f"Intelligent Cron {node_id}"),
                "type": "n8n-nodes-base.cron",
                "typeVersion": 1,
                "position": config.get("position", [200 * node_id, 200]),
                "parameters": {
                    "triggerTimes": {
                        "item": [{
                            "mode": "cronExpression",
                            "cronExpression": config.get("cron", "0 */15 * * * *")  # Every 15 minutes
                        }]
                    }
                },
                "credentials": {},
                "disabled": False,
                "notes": "Intelligent scheduled trigger with adaptive timing"
            }
        
        else:
            # Generic manual trigger
            node = {
                "id": f"trigger-{node_id}",
                "name": config.get("name", f"Manual Trigger {node_id}"),
                "type": "n8n-nodes-base.manualTrigger",
                "typeVersion": 1,
                "position": config.get("position", [200 * node_id, 200]),
                "parameters": {},
                "credentials": {},
                "disabled": False,
                "notes": "Enhanced manual trigger"
            }
        
        return node
    
    def _create_data_transform_node(self, config: Dict[str, Any], node_id: int) -> Dict[str, Any]:
        """Create data transformation node with intelligent processing"""
        
        transform_type = config.get("transform_type", "set")
        
        if transform_type == "set":
            # Enhanced set node with intelligent value setting
            values = config.get("values", {})
            
            set_values = []
            for key, value in values.items():
                set_values.append({
                    "name": key,
                    "value": value,
                    "type": "string" if isinstance(value, str) else "number"
                })
            
            node = {
                "id": f"transform-{node_id}",
                "name": config.get("name", f"Intelligent Transform {node_id}"),
                "type": "n8n-nodes-base.set",
                "typeVersion": 1,
                "position": config.get("position", [200 * node_id, 200]),
                "parameters": {
                    "values": {
                        "string": set_values
                    },
                    "options": {}
                },
                "credentials": {},
                "disabled": False,
                "notes": "Intelligent data transformation with agent context"
            }
        
        else:
            # Function node for custom transformation
            transform_code = f'''
// Intelligent Data Transform
const inputData = items[0].json;
let transformedData = {{ ...inputData }};

// Apply transformations based on agent analysis
if (inputData.agent_analysis) {{
    const agentData = inputData.agent_analysis;
    
    // Apply agent-recommended transformations
    if (agentData.recommendations) {{
        transformedData.agent_recommendations = agentData.recommendations;
    }}
    
    if (agentData.priority_score) {{
        transformedData.priority = agentData.priority_score > 0.8 ? "high" : 
                                  agentData.priority_score > 0.5 ? "medium" : "low";
    }}
}}

// Custom transformation logic
{config.get("custom_code", "// No custom transformation code")}

return [{{ json: transformedData }}];
            '''.strip()
            
            node = {
                "id": f"transform-{node_id}",
                "name": config.get("name", f"Custom Transform {node_id}"),
                "type": "n8n-nodes-base.function",
                "typeVersion": 1,
                "position": config.get("position", [200 * node_id, 200]),
                "parameters": {
                    "functionCode": transform_code,
                    "language": "javascript"
                },
                "credentials": {},
                "disabled": False,
                "notes": "Custom intelligent data transformation"
            }
        
        return node
    
    def _create_action_node(self, config: Dict[str, Any], node_id: int) -> Dict[str, Any]:
        """Create action node with intelligent execution"""
        
        action_type = config.get("action_type", "http")
        
        if action_type == "http":
            node = {
                "id": f"action-{node_id}",
                "name": config.get("name", f"Intelligent HTTP {node_id}"),
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4,
                "position": config.get("position", [200 * node_id, 200]),
                "parameters": {
                    "url": config.get("url", "http://localhost:8787/api/action"),
                    "method": config.get("method", "POST"),
                    "sendHeaders": True,
                    "headerParameters": {
                        "parameters": [
                            {
                                "name": "Content-Type",
                                "value": "application/json"
                            },
                            {
                                "name": "X-Agent-Enhanced",
                                "value": "true"
                            }
                        ]
                    },
                    "sendBody": True,
                    "bodyParameters": {
                        "parameters": config.get("body_params", [])
                    },
                    "options": {
                        "timeout": config.get("timeout", 30000),
                        "retry": {
                            "enabled": True,
                            "maxRetries": 3,
                            "waitBetween": 1000
                        }
                    }
                },
                "credentials": {},
                "disabled": False,
                "notes": "Intelligent HTTP action with retry logic"
            }
        
        elif action_type == "discord":
            # Discord message action
            node = {
                "id": f"action-{node_id}",
                "name": config.get("name", f"Discord Action {node_id}"),
                "type": "n8n-nodes-base.function",
                "typeVersion": 1,
                "position": config.get("position", [200 * node_id, 200]),
                "parameters": {
                    "functionCode": '''
// Intelligent Discord Action
const inputData = items[0].json;
const https = require('https');

// Prepare Discord message with agent context
let message = inputData.message || "Automated message from DuckBot";

// Enhance message with agent analysis if available
if (inputData.agent_analysis && inputData.agent_analysis.reasoning) {
    message += `\\n\\n**AI Analysis:** ${inputData.agent_analysis.reasoning}`;
}

if (inputData.confidence) {
    message += `\\n**Confidence:** ${Math.round(inputData.confidence * 100)}%`;
}

const webhookUrl = process.env.DISCORD_WEBHOOK_URL;
if (!webhookUrl) {
    throw new Error('Discord webhook URL not configured');
}

const payload = JSON.stringify({
    content: message,
    embeds: inputData.agent_analysis ? [{
        title: "AI Enhanced Response",
        color: inputData.confidence > 0.8 ? 0x00ff00 : 0xffaa00,
        fields: [
            {
                name: "Agent Type",
                value: inputData.agent_type || "General",
                inline: true
            },
            {
                name: "Confidence",
                value: `${Math.round((inputData.confidence || 0.5) * 100)}%`,
                inline: true
            }
        ]
    }] : undefined
});

// Send to Discord
const options = {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(payload)
    }
};

return new Promise((resolve, reject) => {
    const req = https.request(webhookUrl, options, (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve([{json: {success: true, message: "Discord message sent"}}]);
        } else {
            reject(new Error(`Discord API error: ${res.statusCode}`));
        }
    });
    
    req.on('error', reject);
    req.write(payload);
    req.end();
});
                    '''.strip(),
                    "language": "javascript"
                },
                "credentials": {},
                "disabled": False,
                "notes": "Enhanced Discord action with agent context"
            }
        
        else:
            # Generic function action
            node = {
                "id": f"action-{node_id}",
                "name": config.get("name", f"Custom Action {node_id}"),
                "type": "n8n-nodes-base.function",
                "typeVersion": 1,
                "position": config.get("position", [200 * node_id, 200]),
                "parameters": {
                    "functionCode": config.get("code", '''
// Custom intelligent action
const inputData = items[0].json;

// Process with agent context awareness
let result = {
    processed: true,
    timestamp: Date.now(),
    agent_enhanced: !!inputData.agent_analysis
};

return [{json: {...inputData, ...result}}];
                    ''').strip(),
                    "language": "javascript"
                },
                "credentials": {},
                "disabled": False,
                "notes": "Custom intelligent action"
            }
        
        return node
    
    def _create_node_connections(self, workflow: Dict[str, Any], config: Dict[str, Any]):
        """Create connections between nodes based on configuration"""
        
        connections = {}
        steps = config.get("steps", [])
        
        # Simple linear connection by default
        for i in range(len(steps) - 1):
            current_step = steps[i]
            next_step = steps[i + 1]
            
            current_node_id = self._get_node_id_from_step(current_step, i + 1)
            next_node_id = self._get_node_id_from_step(next_step, i + 2)
            
            if current_node_id not in connections:
                connections[current_node_id] = {}
            
            connections[current_node_id]["main"] = [[{
                "node": next_node_id,
                "type": "main",
                "index": 0
            }]]
        
        # Handle custom connections from config
        custom_connections = config.get("connections", {})
        for source, targets in custom_connections.items():
            if source not in connections:
                connections[source] = {}
            
            connections[source]["main"] = []
            for target in targets:
                connections[source]["main"].append([{
                    "node": target,
                    "type": "main", 
                    "index": 0
                }])
        
        workflow["connections"] = connections
    
    def _get_node_id_from_step(self, step: Dict[str, Any], node_counter: int) -> str:
        """Get node ID from step configuration"""
        step_type = step.get("type", "unknown")
        return f"{step_type}-{node_counter}"
    
    async def create_agent_helper_script(self) -> str:
        """Create Python helper script for n8n to call agents"""
        
        script_content = '''#!/usr/bin/env python3
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
        '''.strip()
        
        # Write script to temporary file
        script_path = Path.cwd() / "call_agent.py"
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Make executable
        script_path.chmod(0o755)
        
        return str(script_path)
    
    async def deploy_workflow(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy workflow to n8n instance"""
        
        if not self._check_n8n_availability():
            return {"success": False, "error": "n8n not available"}
        
        try:
            # Create agent helper script
            await self.create_agent_helper_script()
            
            # Deploy workflow via n8n API
            response = requests.post(
                f"{self.n8n_url}/api/v1/workflows",
                json=workflow,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                workflow_data = response.json()
                workflow_id = workflow_data.get("id")
                
                # Activate workflow
                if workflow_id:
                    activate_response = requests.patch(
                        f"{self.n8n_url}/api/v1/workflows/{workflow_id}",
                        json={"active": True},
                        timeout=10
                    )
                    
                    if activate_response.status_code == 200:
                        self.active_workflows[workflow_id] = workflow
                        return {
                            "success": True,
                            "workflow_id": workflow_id,
                            "message": "Workflow deployed and activated successfully"
                        }
                
                return {
                    "success": True,
                    "workflow_id": workflow_id,
                    "message": "Workflow deployed but activation failed"
                }
            else:
                return {
                    "success": False,
                    "error": f"n8n API error: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            logger.error(f"Error deploying workflow: {e}")
            return {"success": False, "error": str(e)}
    
    def _check_n8n_availability(self) -> bool:
        """Check if n8n is available"""
        try:
            response = requests.get(f"{self.n8n_url}/healthz", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def create_discord_bot_workflow(self) -> Dict[str, Any]:
        """Create intelligent Discord bot workflow"""
        
        workflow_config = {
            "steps": [
                {
                    "type": "trigger",
                    "trigger_type": "webhook",
                    "name": "Discord Message Trigger",
                    "path": "discord-message",
                    "method": "POST"
                },
                {
                    "type": "ai_agent",
                    "agent_type": "discord_moderator", 
                    "name": "Discord AI Moderator",
                    "confidence_threshold": 0.7
                },
                {
                    "type": "condition",
                    "name": "High Confidence Check",
                    "condition": "confidence > 0.8"
                },
                {
                    "type": "action",
                    "action_type": "discord",
                    "name": "Send Discord Response"
                }
            ]
        }
        
        return self.create_agent_enhanced_workflow("Intelligent Discord Bot", workflow_config)
    
    def create_market_analysis_workflow(self) -> Dict[str, Any]:
        """Create intelligent market analysis workflow"""
        
        workflow_config = {
            "steps": [
                {
                    "type": "trigger",
                    "trigger_type": "schedule",
                    "name": "Market Data Trigger",
                    "cron": "0 */30 * * * *"  # Every 30 minutes
                },
                {
                    "type": "action",
                    "action_type": "http",
                    "name": "Fetch Market Data",
                    "url": "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd",
                    "method": "GET"
                },
                {
                    "type": "ai_agent",
                    "agent_type": "market_analyzer",
                    "name": "Market AI Analyzer",
                    "confidence_threshold": 0.6
                },
                {
                    "type": "condition",
                    "name": "Significant Change Check",
                    "condition": "confidence > 0.75 && (action === 'strong_buy' || action === 'strong_sell')"
                },
                {
                    "type": "action",
                    "action_type": "discord",
                    "name": "Send Market Alert"
                }
            ]
        }
        
        return self.create_agent_enhanced_workflow("Intelligent Market Analysis", workflow_config)


# Global integration instance
n8n_integration = N8nAgentIntegration()

# Convenience functions for easy use
async def create_intelligent_workflow(name: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Create and deploy intelligent workflow"""
    workflow = n8n_integration.create_agent_enhanced_workflow(name, config)
    result = await n8n_integration.deploy_workflow(workflow)
    return result

def create_discord_workflow() -> Dict[str, Any]:
    """Create intelligent Discord workflow"""
    return n8n_integration.create_discord_bot_workflow()

def create_market_workflow() -> Dict[str, Any]:
    """Create intelligent market analysis workflow"""  
    return n8n_integration.create_market_analysis_workflow()

async def deploy_workflow_to_n8n(workflow: Dict[str, Any]) -> Dict[str, Any]:
    """Deploy workflow to n8n"""
    return await n8n_integration.deploy_workflow(workflow)