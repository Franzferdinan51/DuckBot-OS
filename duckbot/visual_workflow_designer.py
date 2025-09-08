"""
DuckBot Visual Workflow Designer
SIM.ai-inspired Figma-like canvas for designing AI agent workflows
"""

import json
import uuid
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class NodeType(Enum):
    """Types of nodes in the visual workflow"""
    TRIGGER = "trigger"
    AI_AGENT = "ai_agent"
    DATA_TRANSFORM = "data_transform"
    API_CALL = "api_call"
    CONDITION = "condition"
    ACTION = "action"
    OUTPUT = "output"
    SUBFLOW = "subflow"

class ConnectionType(Enum):
    """Types of connections between nodes"""
    DATA_FLOW = "data_flow"
    CONDITIONAL = "conditional"
    ERROR_HANDLER = "error_handler"
    PARALLEL = "parallel"

@dataclass
class Position:
    """Position on the visual canvas"""
    x: float
    y: float
    
@dataclass
class Size:
    """Size of visual elements"""
    width: float
    height: float

@dataclass
class VisualNode:
    """Visual node on the workflow canvas"""
    id: str
    type: NodeType
    name: str
    position: Position
    size: Size
    config: Dict[str, Any]
    metadata: Dict[str, Any]
    color: str = "#4A90E2"
    icon: str = "🤖"
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]

@dataclass
class VisualConnection:
    """Connection between visual nodes"""
    id: str
    source_node: str
    source_port: str
    target_node: str
    target_port: str
    type: ConnectionType
    config: Dict[str, Any]
    metadata: Dict[str, Any]
    color: str = "#666666"
    style: str = "solid"
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]

@dataclass
class WorkflowCanvas:
    """Complete visual workflow canvas"""
    id: str
    name: str
    description: str
    nodes: List[VisualNode]
    connections: List[VisualConnection]
    canvas_config: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: float
    updated_at: float
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = time.time()
        if not self.updated_at:
            self.updated_at = time.time()

class VisualWorkflowDesigner:
    """Main class for the visual workflow designer"""
    
    def __init__(self):
        self.canvases: Dict[str, WorkflowCanvas] = {}
        self.node_templates = self._create_node_templates()
        self.canvas_config = {
            "grid_size": 20,
            "snap_to_grid": True,
            "zoom_level": 1.0,
            "canvas_size": {"width": 2000, "height": 1500},
            "theme": "light"
        }
    
    def _create_node_templates(self) -> Dict[NodeType, Dict[str, Any]]:
        """Create templates for different node types"""
        return {
            NodeType.TRIGGER: {
                "name": "Trigger",
                "description": "Workflow trigger event",
                "color": "#E74C3C",
                "icon": "⚡",
                "default_size": Size(120, 60),
                "ports": {
                    "output": ["data_out", "event_out"]
                },
                "config_schema": {
                    "trigger_type": {"type": "select", "options": ["webhook", "schedule", "discord_message", "market_event"]},
                    "trigger_config": {"type": "object"}
                }
            },
            NodeType.AI_AGENT: {
                "name": "AI Agent",
                "description": "Intelligent AI agent processor",
                "color": "#9B59B6",
                "icon": "🧠",
                "default_size": Size(150, 80),
                "ports": {
                    "input": ["data_in", "context_in"],
                    "output": ["result_out", "confidence_out", "reasoning_out"]
                },
                "config_schema": {
                    "agent_type": {"type": "select", "options": ["market_analyzer", "discord_moderator", "workflow_optimizer"]},
                    "confidence_threshold": {"type": "number", "min": 0, "max": 1, "default": 0.7},
                    "learning_enabled": {"type": "boolean", "default": True}
                }
            },
            NodeType.DATA_TRANSFORM: {
                "name": "Data Transform",
                "description": "Transform and process data",
                "color": "#3498DB",
                "icon": "🔧",
                "default_size": Size(140, 70),
                "ports": {
                    "input": ["data_in"],
                    "output": ["data_out"]
                },
                "config_schema": {
                    "transform_type": {"type": "select", "options": ["filter", "map", "aggregate", "format"]},
                    "transform_config": {"type": "object"}
                }
            },
            NodeType.API_CALL: {
                "name": "API Call",
                "description": "Call external API",
                "color": "#F39C12",
                "icon": "🌐",
                "default_size": Size(130, 70),
                "ports": {
                    "input": ["data_in", "params_in"],
                    "output": ["response_out", "error_out"]
                },
                "config_schema": {
                    "url": {"type": "string"},
                    "method": {"type": "select", "options": ["GET", "POST", "PUT", "DELETE"]},
                    "headers": {"type": "object"},
                    "timeout": {"type": "number", "default": 30}
                }
            },
            NodeType.CONDITION: {
                "name": "Condition",
                "description": "Conditional logic branch",
                "color": "#E67E22",
                "icon": "❓",
                "default_size": Size(100, 80),
                "ports": {
                    "input": ["data_in"],
                    "output": ["true_out", "false_out"]
                },
                "config_schema": {
                    "condition_type": {"type": "select", "options": ["equals", "greater_than", "contains", "custom"]},
                    "condition_value": {"type": "any"}
                }
            },
            NodeType.ACTION: {
                "name": "Action",
                "description": "Execute action",
                "color": "#27AE60",
                "icon": "⚙️",
                "default_size": Size(120, 60),
                "ports": {
                    "input": ["trigger_in", "data_in"],
                    "output": ["result_out"]
                },
                "config_schema": {
                    "action_type": {"type": "select", "options": ["send_message", "update_database", "trigger_webhook"]},
                    "action_config": {"type": "object"}
                }
            },
            NodeType.OUTPUT: {
                "name": "Output",
                "description": "Workflow output",
                "color": "#95A5A6",
                "icon": "📤",
                "default_size": Size(100, 50),
                "ports": {
                    "input": ["data_in"]
                },
                "config_schema": {
                    "output_format": {"type": "select", "options": ["json", "text", "webhook"]},
                    "output_config": {"type": "object"}
                }
            }
        }
    
    def create_canvas(self, name: str, description: str = "") -> str:
        """Create a new workflow canvas"""
        canvas = WorkflowCanvas(
            id="",  # Auto-generated
            name=name,
            description=description,
            nodes=[],
            connections=[],
            canvas_config=self.canvas_config.copy(),
            metadata={"created_by": "visual_designer", "version": "1.0"},
            created_at=0,  # Auto-generated
            updated_at=0   # Auto-generated
        )
        
        self.canvases[canvas.id] = canvas
        logger.info(f"Created workflow canvas: {name} ({canvas.id})")
        return canvas.id
    
    def add_node(self, canvas_id: str, node_type: NodeType, position: Position, name: Optional[str] = None, config: Optional[Dict[str, Any]] = None) -> str:
        """Add a node to the canvas"""
        if canvas_id not in self.canvases:
            raise ValueError(f"Canvas {canvas_id} not found")
        
        template = self.node_templates[node_type]
        
        node = VisualNode(
            id="",  # Auto-generated
            type=node_type,
            name=name or template["name"],
            position=position,
            size=template["default_size"],
            config=config or {},
            metadata={"template": template["name"]},
            color=template["color"],
            icon=template["icon"]
        )
        
        self.canvases[canvas_id].nodes.append(node)
        self.canvases[canvas_id].updated_at = time.time()
        
        logger.info(f"Added node {node.id} to canvas {canvas_id}")
        return node.id
    
    def connect_nodes(self, canvas_id: str, source_node: str, source_port: str, target_node: str, target_port: str, connection_type: ConnectionType = ConnectionType.DATA_FLOW, config: Optional[Dict[str, Any]] = None) -> str:
        """Connect two nodes on the canvas"""
        if canvas_id not in self.canvases:
            raise ValueError(f"Canvas {canvas_id} not found")
        
        # Validate nodes exist
        canvas = self.canvases[canvas_id]
        source_found = any(node.id == source_node for node in canvas.nodes)
        target_found = any(node.id == target_node for node in canvas.nodes)
        
        if not source_found or not target_found:
            raise ValueError("Source or target node not found")
        
        connection = VisualConnection(
            id="",  # Auto-generated
            source_node=source_node,
            source_port=source_port,
            target_node=target_node,
            target_port=target_port,
            type=connection_type,
            config=config or {},
            metadata={},
            color="#666666" if connection_type == ConnectionType.DATA_FLOW else "#E74C3C",
            style="solid" if connection_type == ConnectionType.DATA_FLOW else "dashed"
        )
        
        canvas.connections.append(connection)
        canvas.updated_at = time.time()
        
        logger.info(f"Connected {source_node}:{source_port} -> {target_node}:{target_port}")
        return connection.id
    
    def update_node(self, canvas_id: str, node_id: str, updates: Dict[str, Any]) -> bool:
        """Update node properties"""
        if canvas_id not in self.canvases:
            return False
        
        canvas = self.canvases[canvas_id]
        for node in canvas.nodes:
            if node.id == node_id:
                for key, value in updates.items():
                    if hasattr(node, key):
                        if key == "position":
                            node.position = Position(**value) if isinstance(value, dict) else value
                        elif key == "size":
                            node.size = Size(**value) if isinstance(value, dict) else value
                        else:
                            setattr(node, key, value)
                
                canvas.updated_at = time.time()
                return True
        
        return False
    
    def delete_node(self, canvas_id: str, node_id: str) -> bool:
        """Delete a node and its connections"""
        if canvas_id not in self.canvases:
            return False
        
        canvas = self.canvases[canvas_id]
        
        # Remove node
        canvas.nodes = [node for node in canvas.nodes if node.id != node_id]
        
        # Remove connections involving this node
        canvas.connections = [
            conn for conn in canvas.connections
            if conn.source_node != node_id and conn.target_node != node_id
        ]
        
        canvas.updated_at = time.time()
        return True
    
    def get_canvas(self, canvas_id: str) -> Optional[WorkflowCanvas]:
        """Get canvas by ID"""
        return self.canvases.get(canvas_id)
    
    def export_to_n8n(self, canvas_id: str) -> Dict[str, Any]:
        """Export visual workflow to n8n format"""
        canvas = self.canvases.get(canvas_id)
        if not canvas:
            raise ValueError(f"Canvas {canvas_id} not found")
        
        n8n_workflow = {
            "name": canvas.name,
            "nodes": [],
            "connections": {},
            "active": True,
            "settings": {},
            "staticData": {}
        }
        
        # Convert nodes
        for node in canvas.nodes:
            n8n_node = self._convert_node_to_n8n(node)
            n8n_workflow["nodes"].append(n8n_node)
        
        # Convert connections
        connections_map = {}
        for conn in canvas.connections:
            source_node = conn.source_node
            if source_node not in connections_map:
                connections_map[source_node] = {}
            
            if conn.source_port not in connections_map[source_node]:
                connections_map[source_node][conn.source_port] = []
            
            connections_map[source_node][conn.source_port].append({
                "node": conn.target_node,
                "type": "main",
                "index": 0
            })
        
        n8n_workflow["connections"] = connections_map
        
        return n8n_workflow
    
    def _convert_node_to_n8n(self, node: VisualNode) -> Dict[str, Any]:
        """Convert visual node to n8n node format"""
        # Map node types to n8n node types
        type_mapping = {
            NodeType.TRIGGER: "n8n-nodes-base.webhook",
            NodeType.AI_AGENT: "n8n-nodes-base.function",
            NodeType.DATA_TRANSFORM: "n8n-nodes-base.set",
            NodeType.API_CALL: "n8n-nodes-base.httpRequest",
            NodeType.CONDITION: "n8n-nodes-base.if",
            NodeType.ACTION: "n8n-nodes-base.function",
            NodeType.OUTPUT: "n8n-nodes-base.noOp"
        }
        
        n8n_node = {
            "id": str(uuid.uuid4()),
            "name": node.name,
            "type": type_mapping.get(node.type, "n8n-nodes-base.noOp"),
            "typeVersion": 1,
            "position": [node.position.x, node.position.y],
            "parameters": self._convert_config_to_n8n_params(node.type, node.config)
        }
        
        return n8n_node
    
    def _convert_config_to_n8n_params(self, node_type: NodeType, config: Dict[str, Any]) -> Dict[str, Any]:
        """Convert node config to n8n parameters"""
        if node_type == NodeType.AI_AGENT:
            # Convert AI agent config to function node
            agent_code = f"""
// AI Agent: {config.get('agent_type', 'general')}
const agentType = '{config.get('agent_type', 'general')}';
const confidenceThreshold = {config.get('confidence_threshold', 0.7)};

// Import DuckBot intelligent agents
const {{ analyze_with_intelligence }} = require('./duckbot/intelligent_agents');

// Process input data
const inputData = items[0].json;

// Analyze with AI agent
const result = await analyze_with_intelligence(agentType, inputData);

// Return result if confidence is above threshold
if (result.confidence >= confidenceThreshold) {{
    return [{{
        json: {{
            ...result.data,
            confidence: result.confidence,
            reasoning: result.reasoning,
            agent_type: result.agent_type
        }}
    }}];
}} else {{
    return [{{
        json: {{
            error: 'Confidence too low',
            confidence: result.confidence,
            threshold: confidenceThreshold
        }}
    }}];
}}
            """.strip()
            
            return {
                "functionCode": agent_code,
                "language": "javascript"
            }
        
        elif node_type == NodeType.API_CALL:
            return {
                "url": config.get("url", ""),
                "method": config.get("method", "GET"),
                "headers": config.get("headers", {}),
                "timeout": config.get("timeout", 30) * 1000  # n8n uses milliseconds
            }
        
        elif node_type == NodeType.CONDITION:
            return {
                "conditions": {
                    "boolean": [],
                    "number": [],
                    "string": [
                        {
                            "value1": "={{ $json.value }}",
                            "operation": config.get("condition_type", "equals"),
                            "value2": config.get("condition_value", "")
                        }
                    ]
                }
            }
        
        else:
            # Return config as-is for other node types
            return config
    
    def create_ai_workflow_template(self, canvas_id: str) -> Dict[str, str]:
        """Create a template AI-powered workflow"""
        # Add trigger node
        trigger_id = self.add_node(
            canvas_id, 
            NodeType.TRIGGER, 
            Position(100, 100),
            "Discord Message",
            {"trigger_type": "discord_message"}
        )
        
        # Add AI agent node
        agent_id = self.add_node(
            canvas_id,
            NodeType.AI_AGENT,
            Position(300, 100),
            "Discord Moderator",
            {"agent_type": "discord_moderator", "confidence_threshold": 0.7}
        )
        
        # Add condition node
        condition_id = self.add_node(
            canvas_id,
            NodeType.CONDITION,
            Position(500, 100),
            "High Confidence?",
            {"condition_type": "greater_than", "condition_value": 0.8}
        )
        
        # Add action nodes
        action_id = self.add_node(
            canvas_id,
            NodeType.ACTION,
            Position(700, 50),
            "Send Response",
            {"action_type": "send_message"}
        )
        
        fallback_id = self.add_node(
            canvas_id,
            NodeType.ACTION,
            Position(700, 150),
            "Escalate to Human",
            {"action_type": "trigger_webhook"}
        )
        
        # Connect nodes
        self.connect_nodes(canvas_id, trigger_id, "data_out", agent_id, "data_in")
        self.connect_nodes(canvas_id, agent_id, "result_out", condition_id, "data_in")
        self.connect_nodes(canvas_id, condition_id, "true_out", action_id, "trigger_in", ConnectionType.CONDITIONAL)
        self.connect_nodes(canvas_id, condition_id, "false_out", fallback_id, "trigger_in", ConnectionType.CONDITIONAL)
        
        return {
            "trigger": trigger_id,
            "agent": agent_id,
            "condition": condition_id,
            "action": action_id,
            "fallback": fallback_id
        }
    
    def generate_web_ui(self, canvas_id: str) -> str:
        """Generate HTML/JavaScript for web-based canvas editor"""
        canvas = self.canvases.get(canvas_id)
        if not canvas:
            raise ValueError(f"Canvas {canvas_id} not found")
        
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DuckBot Visual Workflow Designer - {canvas.name}</title>
    <style>
        body {{
            margin: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
        }}
        
        .canvas-container {{
            width: 100vw;
            height: 100vh;
            position: relative;
            overflow: hidden;
        }}
        
        .canvas {{
            width: {self.canvas_config['canvas_size']['width']}px;
            height: {self.canvas_config['canvas_size']['height']}px;
            background: white;
            position: relative;
            background-image: 
                linear-gradient(rgba(0,0,0,0.1) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0,0,0,0.1) 1px, transparent 1px);
            background-size: {self.canvas_config['grid_size']}px {self.canvas_config['grid_size']}px;
        }}
        
        .node {{
            position: absolute;
            border: 2px solid #ddd;
            border-radius: 8px;
            background: white;
            padding: 10px;
            cursor: move;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: all 0.2s ease;
            user-select: none;
        }}
        
        .node:hover {{
            box-shadow: 0 4px 16px rgba(0,0,0,0.15);
        }}
        
        .node.selected {{
            border-color: #007bff;
            box-shadow: 0 0 0 3px rgba(0,123,255,0.25);
        }}
        
        .node-header {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .node-icon {{
            font-size: 16px;
        }}
        
        .connection {{
            position: absolute;
            pointer-events: none;
        }}
        
        .sidebar {{
            position: fixed;
            right: 0;
            top: 0;
            width: 300px;
            height: 100vh;
            background: white;
            border-left: 1px solid #ddd;
            padding: 20px;
            overflow-y: auto;
        }}
        
        .toolbar {{
            position: fixed;
            top: 0;
            left: 0;
            right: 300px;
            height: 60px;
            background: white;
            border-bottom: 1px solid #ddd;
            display: flex;
            align-items: center;
            padding: 0 20px;
            gap: 10px;
        }}
        
        .btn {{
            padding: 8px 16px;
            border: 1px solid #ddd;
            border-radius: 4px;
            background: white;
            cursor: pointer;
        }}
        
        .btn:hover {{
            background: #f5f5f5;
        }}
        
        .node-palette {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-bottom: 20px;
        }}
        
        .palette-item {{
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            cursor: pointer;
            text-align: center;
            transition: all 0.2s ease;
        }}
        
        .palette-item:hover {{
            background: #f5f5f5;
            border-color: #007bff;
        }}
    </style>
</head>
<body>
    <div class="toolbar">
        <button class="btn" onclick="exportToN8n()">Export to n8n</button>
        <button class="btn" onclick="saveCanvas()">Save</button>
        <button class="btn" onclick="loadCanvas()">Load</button>
        <span style="margin-left: auto;">
            Zoom: <input type="range" min="0.5" max="2" step="0.1" value="1" onchange="setZoom(this.value)">
        </span>
    </div>
    
    <div class="canvas-container">
        <div class="canvas" id="canvas">
            {self._generate_canvas_html(canvas)}
        </div>
    </div>
    
    <div class="sidebar">
        <h3>Node Palette</h3>
        <div class="node-palette">
            {self._generate_palette_html()}
        </div>
        
        <h3>Properties</h3>
        <div id="properties-panel">
            Select a node to edit properties
        </div>
    </div>
    
    <script>
        {self._generate_canvas_javascript(canvas)}
    </script>
</body>
</html>
        """
        
        return html_template
    
    def _generate_canvas_html(self, canvas: WorkflowCanvas) -> str:
        """Generate HTML for canvas nodes"""
        html = ""
        
        for node in canvas.nodes:
            html += f"""
            <div class="node" id="node-{node.id}" 
                 style="left: {node.position.x}px; top: {node.position.y}px; 
                        width: {node.size.width}px; height: {node.size.height}px;
                        border-color: {node.color};">
                <div class="node-header">
                    <span class="node-icon">{node.icon}</span>
                    <span>{node.name}</span>
                </div>
                <div style="font-size: 12px; color: #666;">
                    {node.type.value.replace('_', ' ').title()}
                </div>
            </div>
            """
        
        return html
    
    def _generate_palette_html(self) -> str:
        """Generate HTML for node palette"""
        html = ""
        
        for node_type, template in self.node_templates.items():
            html += f"""
            <div class="palette-item" onclick="addNodeToCanvas('{node_type.value}')" 
                 style="border-color: {template['color']};">
                <div>{template['icon']}</div>
                <div style="font-size: 12px; margin-top: 5px;">{template['name']}</div>
            </div>
            """
        
        return html
    
    def _generate_canvas_javascript(self, canvas: WorkflowCanvas) -> str:
        """Generate JavaScript for canvas interactivity"""
        return f"""
        let selectedNode = null;
        let isDragging = false;
        let dragOffset = {{x: 0, y: 0}};
        
        // Canvas data
        let canvasData = {json.dumps(asdict(canvas), default=str, indent=2)};
        
        // Node interaction
        document.querySelectorAll('.node').forEach(node => {{
            node.addEventListener('mousedown', startDrag);
            node.addEventListener('click', selectNode);
        }});
        
        function startDrag(e) {{
            isDragging = true;
            selectedNode = e.currentTarget;
            const rect = selectedNode.getBoundingClientRect();
            dragOffset.x = e.clientX - rect.left;
            dragOffset.y = e.clientY - rect.top;
            
            document.addEventListener('mousemove', drag);
            document.addEventListener('mouseup', stopDrag);
        }}
        
        function drag(e) {{
            if (!isDragging || !selectedNode) return;
            
            const canvas = document.getElementById('canvas');
            const canvasRect = canvas.getBoundingClientRect();
            
            let x = e.clientX - canvasRect.left - dragOffset.x;
            let y = e.clientY - canvasRect.top - dragOffset.y;
            
            // Snap to grid
            const gridSize = {self.canvas_config['grid_size']};
            if ({str(self.canvas_config['snap_to_grid']).lower()}) {{
                x = Math.round(x / gridSize) * gridSize;
                y = Math.round(y / gridSize) * gridSize;
            }}
            
            selectedNode.style.left = x + 'px';
            selectedNode.style.top = y + 'px';
        }}
        
        function stopDrag() {{
            isDragging = false;
            selectedNode = null;
            document.removeEventListener('mousemove', drag);
            document.removeEventListener('mouseup', stopDrag);
        }}
        
        function selectNode(e) {{
            // Remove previous selection
            document.querySelectorAll('.node').forEach(n => n.classList.remove('selected'));
            
            // Select current node
            e.currentTarget.classList.add('selected');
            
            // Update properties panel
            updatePropertiesPanel(e.currentTarget.id);
        }}
        
        function updatePropertiesPanel(nodeId) {{
            const panel = document.getElementById('properties-panel');
            const node = canvasData.nodes.find(n => `node-${{n.id}}` === nodeId);
            
            if (node) {{
                panel.innerHTML = `
                    <div><strong>${{node.name}}</strong></div>
                    <div>Type: ${{node.type}}</div>
                    <div>Position: (${{node.position.x}}, ${{node.position.y}})</div>
                    <div>Size: ${{node.size.width}} x ${{node.size.height}}</div>
                `;
            }}
        }}
        
        function addNodeToCanvas(nodeType) {{
            // Add node at center of viewport
            const x = window.innerWidth / 2 - 150;  // Account for sidebar
            const y = window.innerHeight / 2 - 60;  // Account for toolbar
            
            fetch('/api/add_node', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{
                    canvas_id: canvasData.id,
                    node_type: nodeType,
                    position: {{x, y}}
                }})
            }}).then(() => location.reload());
        }}
        
        function exportToN8n() {{
            fetch('/api/export_n8n/' + canvasData.id)
                .then(response => response.json())
                .then(data => {{
                    const blob = new Blob([JSON.stringify(data, null, 2)], {{type: 'application/json'}});
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = canvasData.name + '_n8n_workflow.json';
                    a.click();
                }});
        }}
        
        function saveCanvas() {{
            fetch('/api/save_canvas/' + canvasData.id, {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify(canvasData)
            }}).then(() => alert('Canvas saved!'));
        }}
        
        function setZoom(value) {{
            document.getElementById('canvas').style.transform = `scale(${{value}})`;
        }}
        """
    
    def save_canvas(self, canvas_id: str, file_path: Optional[str] = None) -> bool:
        """Save canvas to JSON file"""
        canvas = self.canvases.get(canvas_id)
        if not canvas:
            return False
        
        file_path = file_path or f"workflow_{canvas_id}.json"
        
        try:
            with open(file_path, 'w') as f:
                json.dump(asdict(canvas), f, indent=2, default=str)
            return True
        except Exception as e:
            logger.error(f"Error saving canvas: {e}")
            return False
    
    def load_canvas(self, file_path: str) -> Optional[str]:
        """Load canvas from JSON file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Reconstruct canvas object
            canvas = WorkflowCanvas(
                id=data["id"],
                name=data["name"],
                description=data["description"],
                nodes=[
                    VisualNode(
                        id=node["id"],
                        type=NodeType(node["type"]),
                        name=node["name"],
                        position=Position(**node["position"]),
                        size=Size(**node["size"]),
                        config=node["config"],
                        metadata=node["metadata"],
                        color=node["color"],
                        icon=node["icon"]
                    ) for node in data["nodes"]
                ],
                connections=[
                    VisualConnection(
                        id=conn["id"],
                        source_node=conn["source_node"],
                        source_port=conn["source_port"],
                        target_node=conn["target_node"],
                        target_port=conn["target_port"],
                        type=ConnectionType(conn["type"]),
                        config=conn["config"],
                        metadata=conn["metadata"],
                        color=conn["color"],
                        style=conn["style"]
                    ) for conn in data["connections"]
                ],
                canvas_config=data["canvas_config"],
                metadata=data["metadata"],
                created_at=data["created_at"],
                updated_at=data["updated_at"]
            )
            
            self.canvases[canvas.id] = canvas
            return canvas.id
            
        except Exception as e:
            logger.error(f"Error loading canvas: {e}")
            return None


# Global designer instance
visual_designer = VisualWorkflowDesigner()

# Convenience functions for easy integration
def create_workflow(name: str, description: str = "") -> str:
    """Create new visual workflow"""
    return visual_designer.create_canvas(name, description)

def add_ai_agent_node(canvas_id: str, position: Tuple[float, float], agent_type: str = "general") -> str:
    """Add AI agent node to workflow"""
    return visual_designer.add_node(
        canvas_id, 
        NodeType.AI_AGENT, 
        Position(*position),
        f"AI Agent ({agent_type})",
        {"agent_type": agent_type}
    )

def export_workflow_to_n8n(canvas_id: str) -> Dict[str, Any]:
    """Export visual workflow to n8n format"""
    return visual_designer.export_to_n8n(canvas_id)

def create_smart_discord_workflow(canvas_id: str) -> Dict[str, str]:
    """Create AI-powered Discord workflow template"""
    return visual_designer.create_ai_workflow_template(canvas_id)

def generate_workflow_ui(canvas_id: str) -> str:
    """Generate web UI for workflow designer"""
    return visual_designer.generate_web_ui(canvas_id)