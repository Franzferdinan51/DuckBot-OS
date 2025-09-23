#!/usr/bin/env python3
"""
Qwen3-Omni-UI WebSocket Configuration
Defines WebSocket endpoints and real-time communication settings
"""

import os
from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class WebSocketEndpoint:
    """WebSocket endpoint configuration"""
    path: str
    port: int
    host: str = "127.0.0.1"
    enabled: bool = True
    max_connections: int = 100
    timeout: int = 30

@dataclass
class Qwen3OmniWebSocketConfig:
    """Qwen3-Omni-UI WebSocket configuration"""

    # WebSocket endpoints
    endpoints: Dict[str, WebSocketEndpoint] = None

    # Default settings
    default_host: str = "127.0.0.1"
    default_port: int = 8796
    default_path: str = "/ws"
    max_concurrent_connections: int = 50
    connection_timeout: int = 30
    heartbeat_interval: int = 30
    message_queue_size: int = 1000

    def __post_init__(self):
        if self.endpoints is None:
            self.endpoints = {
                "main": WebSocketEndpoint(
                    path="/ws",
                    port=8796,
                    host="127.0.0.1",
                    enabled=True,
                    max_connections=50,
                    timeout=30
                ),
                "chat": WebSocketEndpoint(
                    path="/ws/chat",
                    port=8796,
                    host="127.0.0.1",
                    enabled=True,
                    max_connections=25,
                    timeout=30
                ),
                "monitoring": WebSocketEndpoint(
                    path="/ws/monitoring",
                    port=8796,
                    host="127.0.0.1",
                    enabled=True,
                    max_connections=10,
                    timeout=30
                ),
                "ai_status": WebSocketEndpoint(
                    path="/ws/ai-status",
                    port=8796,
                    host="127.0.0.1",
                    enabled=True,
                    max_connections=15,
                    timeout=30
                )
            }

    def get_endpoint_url(self, endpoint_name: str = "main") -> str:
        """Get WebSocket URL for endpoint"""
        endpoint = self.endpoints.get(endpoint_name)
        if not endpoint or not endpoint.enabled:
            return None

        return f"ws://{endpoint.host}:{endpoint.port}{endpoint.path}"

    def get_all_endpoints(self) -> Dict[str, str]:
        """Get all enabled WebSocket endpoints"""
        return {
            name: self.get_endpoint_url(name)
            for name, endpoint in self.endpoints.items()
            if endpoint.enabled
        }

    def update_endpoint(self, name: str, **kwargs):
        """Update endpoint configuration"""
        if name in self.endpoints:
            endpoint = self.endpoints[name]
            for key, value in kwargs.items():
                if hasattr(endpoint, key):
                    setattr(endpoint, key, value)

# Global configuration instance
qwen3_omni_ws_config = Qwen3OmniWebSocketConfig()

# Environment variable overrides
def load_from_env():
    """Load configuration from environment variables"""
    config = qwen3_omni_ws_config

    # Override with environment variables
    config.default_host = os.getenv("QWEN3_OMNI_WS_HOST", config.default_host)
    config.default_port = int(os.getenv("QWEN3_OMNI_WS_PORT", config.default_port))
    config.default_path = os.getenv("QWEN3_OMNI_WS_PATH", config.default_path)
    config.max_concurrent_connections = int(os.getenv("QWEN3_OMNI_MAX_CONCURRENT", config.max_concurrent_connections))
    config.connection_timeout = int(os.getenv("QWEN3_OMNI_TIMEOUT", config.connection_timeout))

    # Update main endpoint
    config.update_endpoint("main",
        host=config.default_host,
        port=config.default_port,
        path=config.default_path,
        max_connections=config.max_concurrent_connections,
        timeout=config.connection_timeout
    )

# Load configuration on import
load_from_env()

if __name__ == "__main__":
    # Test configuration
    print("=== Qwen3-Omni-UI WebSocket Configuration ===")
    print()

    print("Enabled endpoints:")
    for name, url in qwen3_omni_ws_config.get_all_endpoints().items():
        print(f"  {name}: {url}")

    print()
    print(f"Default host: {qwen3_omni_ws_config.default_host}")
    print(f"Default port: {qwen3_omni_ws_config.default_port}")
    print(f"Max concurrent connections: {qwen3_omni_ws_config.max_concurrent_connections}")
    print(f"Connection timeout: {qwen3_omni_ws_config.connection_timeout}s")