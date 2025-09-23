#!/usr/bin/env python3
"""
DuckBot Port Allocation Configuration
Defines comprehensive port allocation strategy for all services
"""

import os
from typing import Dict, NamedTuple
from dataclasses import dataclass

@dataclass
class PortRange:
    """Port range configuration"""
    start: int
    end: int
    description: str

@dataclass
class ServicePort:
    """Service port configuration"""
    service: str
    port: int
    description: str
    protocol: str = "http"
    required: bool = True

class DuckBotPortAllocator:
    """Comprehensive port allocation manager"""

    # Port ranges for different service types
    PORT_RANGES = {
        "core": PortRange(8780, 8789, "Core DuckBot services"),
        "websocket": PortRange(8790, 8799, "WebSocket services"),
        "monitoring": PortRange(8800, 8809, "Monitoring and diagnostics"),
        "integration": PortRange(8810, 8819, "Third-party integrations"),
        "development": PortRange(3000, 3099, "Development servers"),
        "testing": PortRange(8820, 8829, "Testing services")
    }

    # Standard service port allocations
    SERVICE_PORTS = {
        # Core Services
        "webui": ServicePort("WebUI", 8787, "Main DuckBot WebUI", "http", True),
        "qwen3_omni_ui": ServicePort("Qwen3-Omni-UI", 8788, "Qwen3-Omni advanced UI interface", "http", True),
        "monitoring": ServicePort("Monitoring", 8789, "AI Ecosystem Manager", "http", True),
        "ai_router": ServicePort("AI Router", 8790, "AI routing and management", "http", True),

        # WebSocket Services
        "websocket_mcp": ServicePort("WebSocket MCP", 8791, "WebSocket MCP server", "ws", True),
        "websocket_chat": ServicePort("WebSocket Chat", 8792, "WebSocket chat server", "ws", True),
        "websocket_api": ServicePort("WebSocket API", 8793, "WebSocket API gateway", "ws", False),
        "qwen3_omni_ws": ServicePort("Qwen3-Omni WebSocket", 8796, "Qwen3-Omni WebSocket endpoint", "ws", True),

        # MCP Server (dedicated)
        "mcp_server": ServicePort("MCP Server", 8794, "Dedicated MCP server", "http", True),
        "mcp_websocket": ServicePort("MCP WebSocket", 8795, "MCP WebSocket endpoint", "ws", True),

        # Monitoring Services
        "health_monitor": ServicePort("Health Monitor", 8800, "Service health monitoring", "http", False),
        "metrics_collector": ServicePort("Metrics Collector", 8801, "Performance metrics", "http", False),
        "log_aggregator": ServicePort("Log Aggregator", 8802, "Central logging", "http", False),

        # Development Servers
        "react_dev": ServicePort("React Dev Server", 3000, "React development server", "http", False),
        "hot_reload": ServicePort("Hot Reload", 3001, "Hot reload server", "http", False),

        # Testing Services
        "test_server": ServicePort("Test Server", 8820, "Testing server", "http", False),
        "mock_server": ServicePort("Mock Server", 8821, "Mock API server", "http", False),

        # Legacy/Compatibility
        "classic_enhanced": ServicePort("Classic Enhanced", 8792, "Classic enhanced UI (legacy)", "http", False),
        "ai_dashboard": ServicePort("AI Dashboard", 8791, "AI dashboard (legacy)", "http", False),
    }

    def __init__(self):
        self.allocated_ports = set()
        self.port_conflicts = []

    def allocate_port(self, service_name: str, preferred_port: int = None) -> int:
        """Allocate a port for a service"""
        if service_name in self.SERVICE_PORTS:
            service = self.SERVICE_PORTS[service_name]
            if self._is_port_available(service.port):
                self.allocated_ports.add(service.port)
                return service.port
            else:
                self.port_conflicts.append(f"Port {service.port} for {service_name} is already in use")
                # Find alternative port in the same range
                return self._find_alternative_port(service.port)

        # Custom service allocation
        if preferred_port and self._is_port_available(preferred_port):
            self.allocated_ports.add(preferred_port)
            return preferred_port

        # Find available port in development range
        return self._find_available_port(3000, 3099)

    def _is_port_available(self, port: int) -> bool:
        """Check if port is available"""
        if port in self.allocated_ports:
            return False

        # Check if port is in use by system
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.1)
                result = s.connect_ex(('localhost', port))
                return result != 0
        except:
            return False

    def _find_alternative_port(self, original_port: int) -> int:
        """Find alternative port near original"""
        for offset in range(1, 10):
            alt_port = original_port + offset
            if self._is_port_available(alt_port):
                self.allocated_ports.add(alt_port)
                return alt_port
        return original_port  # Fallback to original

    def _find_available_port(self, start: int, end: int) -> int:
        """Find available port in range"""
        for port in range(start, end + 1):
            if self._is_port_available(port):
                self.allocated_ports.add(port)
                return port
        return start  # Fallback to start

    def get_service_port(self, service_name: str) -> int:
        """Get port for specific service"""
        return self.SERVICE_PORTS.get(service_name, ServicePort(service_name, 8000, "Default")).port

    def get_port_allocations(self) -> Dict[str, int]:
        """Get all port allocations"""
        return {service: self.allocate_port(service) for service in self.SERVICE_PORTS}

    def validate_ports(self) -> bool:
        """Validate port allocations"""
        allocations = self.get_port_allocations()
        port_count = {}

        for service, port in allocations.items():
            port_count[port] = port_count.get(port, 0) + 1
            if port_count[port] > 1:
                self.port_conflicts.append(f"Port {port} is allocated to multiple services")
                return False

        return len(self.port_conflicts) == 0

    def get_conflicts(self) -> list:
        """Get port conflicts"""
        return self.port_conflicts

    def get_service_url(self, service_name: str, host: str = "localhost") -> str:
        """Get service URL"""
        service = self.SERVICE_PORTS.get(service_name)
        if not service:
            return None

        port = self.allocate_port(service_name)
        if service.protocol == "ws":
            return f"ws://{host}:{port}"
        else:
            return f"http://{host}:{port}"

# Global instance
port_allocator = DuckBotPortAllocator()

# Environment variable overrides
def get_port_from_env(service_name: str, default: int) -> int:
    """Get port from environment variable"""
    env_var = f"DUCKBOT_{service_name.upper()}_PORT"
    return int(os.getenv(env_var, default))

# Standard port exports
DUCKBOT_WEBUI_PORT = get_port_from_env("webui", 8787)
DUCKBOT_QWEN3_OMNI_UI_PORT = get_port_from_env("qwen3_omni_ui", 8788)
DUCKBOT_MONITORING_PORT = get_port_from_env("monitoring", 8789)
DUCKBOT_AI_ROUTER_PORT = get_port_from_env("ai_router", 8790)
DUCKBOT_WEBSOCKET_MCP_PORT = get_port_from_env("websocket_mcp", 8791)
DUCKBOT_WEBSOCKET_CHAT_PORT = get_port_from_env("websocket_chat", 8792)
DUCKBOT_QWEN3_OMNI_WS_PORT = get_port_from_env("qwen3_omni_ws", 8796)
DUCKBOT_MCP_SERVER_PORT = get_port_from_env("mcp_server", 8794)
DUCKBOT_REACT_DEV_PORT = get_port_from_env("react_dev", 3000)

if __name__ == "__main__":
    # Validate port allocation
    allocator = DuckBotPortAllocator()

    print("=== DuckBot Port Allocation Report ===")
    print()

    # Show all allocations
    allocations = allocator.get_port_allocations()
    for service, port in sorted(allocations.items()):
        service_info = allocator.SERVICE_PORTS.get(service)
        if service_info:
            print(f"{service_info.description:25} : {port:>5} ({service_info.protocol})")

    print()

    # Check for conflicts
    if allocator.validate_ports():
        print("✅ All port allocations are valid")
    else:
        print("❌ Port conflicts found:")
        for conflict in allocator.get_conflicts():
            print(f"   - {conflict}")

    print()
    print("Environment variable overrides available:")
    for service in ["webui", "monitoring", "ai_router", "websocket_mcp", "websocket_chat", "mcp_server", "react_dev"]:
        env_var = f"DUCKBOT_{service.upper()}_PORT"
        print(f"   {env_var}")