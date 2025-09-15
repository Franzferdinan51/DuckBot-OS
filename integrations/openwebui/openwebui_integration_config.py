"""
OpenWebUI-DuckBot Integration Configuration
Enhanced with Archon-inspired features for advanced knowledge management
"""

import os
import json
import asyncio
import aiohttp
from pathlib import Path
from typing import Dict, List, Optional
import yaml

class OpenWebUIConfig:
    """Configuration manager for OpenWebUI-DuckBot integration"""
    
    def __init__(self):
        self.config_path = Path("openwebui_duckbot_config.yaml")
        self.default_config = {
            "adapter": {
                "host": "127.0.0.1",
                "port": 11434,
                "timeout": 60,
                "max_connections": 100
            },
            "duckbot": {
                "webui_url": "http://localhost:8787",
                "default_task_type": "auto",
                "enable_rag": True,
                "enable_qwen": True,
                "enable_cost_tracking": True
            },
            "models": {
                "auto_refresh": True,
                "refresh_interval": 300,  # 5 minutes
                "include_lm_studio": True,
                "model_mapping": {
                    "gpt-3.5-turbo": "duckbot-auto",
                    "gpt-4": "duckbot-reasoning",
                    "claude": "duckbot-qwen"
                }
            },
            "features": {
                "streaming": True,
                "conversation_context": True,
                "rag_integration": True,
                "code_analysis": True,
                "voice_synthesis": True,
                "cost_analytics": True
            },
            "archon_features": {
                "smart_search": True,
                "project_management": False,
                "document_processing": True,
                "collaborative_updates": False,
                "version_control": False
            },
            "openwebui": {
                "compatibility_mode": "ollama",
                "model_prefix": "duckbot-",
                "enable_system_messages": True,
                "max_context_length": 4096
            }
        }
    
    def load_config(self) -> Dict:
        """Load configuration from file or create default"""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            self.save_config(self.default_config)
            return self.default_config
    
    def save_config(self, config: Dict):
        """Save configuration to file"""
        with open(self.config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
    
    def update_config(self, updates: Dict):
        """Update configuration with new values"""
        config = self.load_config()
        self._deep_update(config, updates)
        self.save_config(config)
    
    def _deep_update(self, base_dict, update_dict):
        """Recursively update nested dictionary"""
        for key, value in update_dict.items():
            if isinstance(value, dict) and key in base_dict:
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value

class AdvancedKnowledgeManager:
    """Enhanced knowledge management inspired by Archon"""
    
    def __init__(self, duckbot_url: str):
        self.duckbot_url = duckbot_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def smart_search(self, query: str, search_types: List[str] = None) -> Dict:
        """Advanced search with multiple strategies (Archon-inspired)"""
        if not search_types:
            search_types = ["rag", "semantic", "contextual"]
        
        results = {"query": query, "strategies": {}}
        
        # RAG search
        if "rag" in search_types:
            try:
                rag_result = await self._rag_search(query)
                results["strategies"]["rag"] = rag_result
            except Exception as e:
                results["strategies"]["rag"] = {"error": str(e)}
        
        # Semantic search (enhanced)
        if "semantic" in search_types:
            try:
                semantic_result = await self._semantic_search(query)
                results["strategies"]["semantic"] = semantic_result
            except Exception as e:
                results["strategies"]["semantic"] = {"error": str(e)}
        
        # Contextual search
        if "contextual" in search_types:
            try:
                contextual_result = await self._contextual_search(query)
                results["strategies"]["contextual"] = contextual_result
            except Exception as e:
                results["strategies"]["contextual"] = {"error": str(e)}
        
        return results
    
    async def _rag_search(self, query: str) -> Dict:
        """RAG search using DuckBot"""
        token_response = await self.session.get(f"{self.duckbot_url}/token")
        token = (await token_response.json()).get("token")
        
        if not token:
            raise Exception("Could not get DuckBot token")
        
        headers = {"Authorization": f"Bearer {token}"}
        data = {"q": query, "top_k": 10}
        
        async with self.session.post(
            f"{self.duckbot_url}/rag/search",
            headers=headers,
            data=data
        ) as response:
            return await response.json()
    
    async def _semantic_search(self, query: str) -> Dict:
        """Enhanced semantic search"""
        # This would integrate with advanced embedding models
        return {
            "method": "semantic_embedding",
            "query": query,
            "note": "Enhanced semantic search would be implemented here"
        }
    
    async def _contextual_search(self, query: str) -> Dict:
        """Contextual search with conversation awareness"""
        return {
            "method": "contextual_awareness",
            "query": query,
            "note": "Contextual search with conversation history would be implemented here"
        }
    
    async def process_document(self, file_path: str, doc_type: str = "auto") -> Dict:
        """Process and index documents (Archon-inspired)"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")
        
        # Document processing logic
        result = {
            "file_path": str(file_path),
            "file_size": file_path.stat().st_size,
            "doc_type": doc_type,
            "processing_status": "queued"
        }
        
        # Here you would implement actual document processing
        # - PDF extraction
        # - Text chunking
        # - Embedding generation
        # - Index updating
        
        return result
    
    async def get_knowledge_stats(self) -> Dict:
        """Get knowledge base statistics"""
        try:
            token_response = await self.session.get(f"{self.duckbot_url}/token")
            token = (await token_response.json()).get("token")
            
            if not token:
                return {"error": "Could not get DuckBot token"}
            
            headers = {"Authorization": f"Bearer {token}"}
            
            # This would call DuckBot's index stats
            # For now, return mock data
            return {
                "total_documents": 0,
                "total_chunks": 0,
                "index_size": "0 MB",
                "last_updated": "N/A"
            }
            
        except Exception as e:
            return {"error": str(e)}

class IntegrationSetup:
    """Setup and configuration utilities"""
    
    @staticmethod
    def generate_openwebui_model_config() -> Dict:
        """Generate model configuration for OpenWebUI"""
        return {
            "models": [
                {
                    "id": "duckbot-auto",
                    "name": "DuckBot Auto Router",
                    "description": "Intelligent AI routing with automatic model selection",
                    "capabilities": ["chat", "code", "reasoning", "search"],
                    "context_length": 4096
                },
                {
                    "id": "duckbot-code", 
                    "name": "DuckBot Code Specialist",
                    "description": "Specialized for code analysis, generation, and debugging",
                    "capabilities": ["code", "debug", "analysis"],
                    "context_length": 4096
                },
                {
                    "id": "duckbot-reasoning",
                    "name": "DuckBot Reasoning Expert", 
                    "description": "Advanced reasoning and problem-solving capabilities",
                    "capabilities": ["reasoning", "analysis", "planning"],
                    "context_length": 4096
                },
                {
                    "id": "duckbot-summary",
                    "name": "DuckBot Summary Generator",
                    "description": "Efficient summarization and information extraction",
                    "capabilities": ["summarization", "extraction"],
                    "context_length": 4096
                },
                {
                    "id": "duckbot-long-form",
                    "name": "DuckBot Long-form Writer", 
                    "description": "Long-form content creation and detailed explanations",
                    "capabilities": ["writing", "content", "detailed"],
                    "context_length": 8192
                },
                {
                    "id": "duckbot-qwen",
                    "name": "DuckBot Qwen Enhanced",
                    "description": "Qwen-enhanced AI with advanced capabilities",
                    "capabilities": ["enhanced", "analysis", "code", "reasoning"],
                    "context_length": 4096
                }
            ]
        }
    
    @staticmethod
    def create_startup_script() -> str:
        """Generate startup script for the integration"""
        return '''#!/bin/bash
# OpenWebUI-DuckBot Integration Startup Script

echo "Starting OpenWebUI-DuckBot Integration..."

# Check if DuckBot is running
if ! curl -s http://localhost:8787/token > /dev/null; then
    echo "Warning: DuckBot WebUI not running. Starting in mock mode."
fi

# Start the adapter
python openwebui_duckbot_adapter.py &
ADAPTER_PID=$!

# Wait for adapter to start
sleep 3

# Check if adapter is running
if curl -s http://localhost:11434/health > /dev/null; then
    echo "[OK] Adapter running successfully at http://localhost:11434"
    echo "Configure OpenWebUI to use: http://127.0.0.1:11434"
else
    echo "[FAIL] Failed to start adapter"
    kill $ADAPTER_PID 2>/dev/null
    exit 1
fi

# Keep running
wait $ADAPTER_PID
'''
    
    @staticmethod
    def create_docker_compose() -> str:
        """Generate Docker Compose configuration"""
        return '''version: '3.8'

services:
  duckbot-adapter:
    build: .
    ports:
      - "11434:11434"
    environment:
      - DUCKBOT_URL=http://host.docker.internal:8787
    volumes:
      - ./config:/app/config
    depends_on:
      - duckbot
    restart: unless-stopped
    
  duckbot:
    # DuckBot container configuration would go here
    # This assumes DuckBot has a Docker image
    ports:
      - "8787:8787"
    restart: unless-stopped
    
  openwebui:
    image: ghcr.io/open-webui/open-webui:main
    ports:
      - "3000:8080"
    environment:
      - OLLAMA_BASE_URL=http://duckbot-adapter:11434
    volumes:
      - openwebui:/app/backend/data
    restart: unless-stopped

volumes:
  openwebui:
'''

async def main():
    """Main setup and test function"""
    print("OpenWebUI-DuckBot Integration Setup")
    print("=" * 50)
    
    # Initialize configuration
    config_manager = OpenWebUIConfig()
    config = config_manager.load_config()
    
    print(f"[OK] Configuration loaded from {config_manager.config_path}")
    print(f"   Adapter will run on {config['adapter']['host']}:{config['adapter']['port']}")
    
    # Test DuckBot connection
    duckbot_url = config['duckbot']['webui_url']
    print(f"\n[EMOJI] Testing DuckBot connection at {duckbot_url}...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{duckbot_url}/token", timeout=5) as response:
                if response.status == 200:
                    print("[OK] DuckBot WebUI is accessible")
                else:
                    print(f"[WARN]  DuckBot WebUI returned status {response.status}")
    except Exception as e:
        print(f"[FAIL] Could not connect to DuckBot: {e}")
    
    # Test advanced features
    print("\n[EMOJI] Testing advanced knowledge management...")
    async with AdvancedKnowledgeManager(duckbot_url) as knowledge_manager:
        try:
            stats = await knowledge_manager.get_knowledge_stats()
            print(f"[OK] Knowledge base stats: {stats}")
        except Exception as e:
            print(f"[WARN]  Knowledge management test failed: {e}")
    
    # Generate configuration files
    print("\n[EMOJI] Generating configuration files...")
    
    # Model configuration
    model_config = IntegrationSetup.generate_openwebui_model_config()
    with open("openwebui_model_config.json", "w") as f:
        json.dump(model_config, f, indent=2)
    print("[OK] Generated openwebui_model_config.json")
    
    # Startup script
    startup_script = IntegrationSetup.create_startup_script()
    with open("start_integration.sh", "w") as f:
        f.write(startup_script)
    os.chmod("start_integration.sh", 0o755)
    print("[OK] Generated start_integration.sh")
    
    # Docker Compose
    docker_compose = IntegrationSetup.create_docker_compose()
    with open("docker-compose.yml", "w") as f:
        f.write(docker_compose)
    print("[OK] Generated docker-compose.yml")
    
    print("\n[SUCCESS] Setup complete! Use START_OPENWEBUI_DUCKBOT_ADAPTER.bat to launch the integration.")

if __name__ == "__main__":
    asyncio.run(main())