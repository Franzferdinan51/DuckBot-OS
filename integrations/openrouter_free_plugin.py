"""
OpenWebUI Plugin for OpenRouter Free Models
Provides access to OpenRouter's free models through OpenWebUI interface
"""

import json
import requests
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class OpenRouterFreePlugin:
    """OpenWebUI Plugin for OpenRouter Free Models"""
    
    def __init__(self):
        self.plugin_info = {
            "id": "openrouter-free",
            "name": "OpenRouter Free Models",
            "version": "1.0.0", 
            "description": "Access OpenRouter's free AI models",
            "author": "DuckBot",
            "url": "https://openrouter.ai"
        }
        
        # OpenRouter free models
        self.free_models = [
            {
                "id": "microsoft/phi-3-mini-128k-instruct:free",
                "name": "Phi-3 Mini 128K (Free)",
                "context_length": 128000,
                "pricing": {"prompt": "0", "completion": "0"}
            },
            {
                "id": "google/gemma-7b-it:free", 
                "name": "Gemma 7B IT (Free)",
                "context_length": 8192,
                "pricing": {"prompt": "0", "completion": "0"}
            },
            {
                "id": "meta-llama/llama-3-8b-instruct:free",
                "name": "Llama 3 8B Instruct (Free)", 
                "context_length": 8192,
                "pricing": {"prompt": "0", "completion": "0"}
            },
            {
                "id": "mistralai/mistral-7b-instruct:free",
                "name": "Mistral 7B Instruct (Free)",
                "context_length": 32768,
                "pricing": {"prompt": "0", "completion": "0"}
            },
            {
                "id": "huggingfaceh4/zephyr-7b-beta:free",
                "name": "Zephyr 7B Beta (Free)",
                "context_length": 32768,
                "pricing": {"prompt": "0", "completion": "0"}
            },
            {
                "id": "nousresearch/nous-capybara-7b:free",
                "name": "Nous Capybara 7B (Free)",
                "context_length": 4096,
                "pricing": {"prompt": "0", "completion": "0"}
            },
            {
                "id": "openchat/openchat-7b:free",
                "name": "OpenChat 7B (Free)",
                "context_length": 8192,
                "pricing": {"prompt": "0", "completion": "0"}
            }
        ]
        
        self.base_url = "https://openrouter.ai/api/v1"
        
    def get_models(self) -> List[Dict[str, Any]]:
        """Get list of available free models"""
        return self.free_models
    
    def get_plugin_info(self) -> Dict[str, Any]:
        """Get plugin information"""
        return self.plugin_info
    
    def validate_model(self, model_id: str) -> bool:
        """Check if model is a valid free model"""
        return any(model["id"] == model_id for model in self.free_models)
    
    def format_for_openwebui(self) -> Dict[str, Any]:
        """Format plugin data for OpenWebUI"""
        return {
            "plugin_info": self.plugin_info,
            "models": self.free_models,
            "api_endpoint": self.base_url,
            "authentication": {
                "type": "header",
                "header": "Authorization",
                "prefix": "Bearer ",
                "required": False,  # Free tier doesn't require API key
                "description": "Optional API key for rate limits and priority access"
            },
            "capabilities": [
                "chat_completion",
                "streaming",
                "system_messages",
                "temperature_control",
                "max_tokens_control"
            ],
            "settings": {
                "default_model": "microsoft/phi-3-mini-128k-instruct:free",
                "max_tokens": 4000,
                "temperature": 0.7,
                "stream": True,
                "show_pricing": True
            }
        }

def create_openwebui_plugin_manifest():
    """Create OpenWebUI plugin manifest"""
    plugin = OpenRouterFreePlugin()
    
    manifest = {
        "manifest_version": 1,
        "id": "openrouter_free",
        "name": "OpenRouter Free Models",
        "version": "1.0.0",
        "description": "Access OpenRouter's free AI models directly in OpenWebUI",
        "author": "DuckBot",
        "homepage_url": "https://openrouter.ai",
        "permissions": ["activeTab", "storage"],
        "content_scripts": [{
            "matches": ["http://localhost:8080/*", "https://localhost:8080/*"],
            "js": ["openrouter_free.js"],
            "css": ["openrouter_free.css"]
        }],
        "background": {
            "scripts": ["background.js"],
            "persistent": False
        },
        "web_accessible_resources": ["icons/*"],
        "icons": {
            "16": "icons/icon16.png",
            "48": "icons/icon48.png", 
            "128": "icons/icon128.png"
        }
    }
    
    return manifest

def create_openwebui_tool_config():
    """Create OpenWebUI tool configuration for OpenRouter free models"""
    
    tool_config = {
        "name": "OpenRouter Free Models",
        "description": "Access to OpenRouter's free AI models",
        "type": "api_provider",
        "config": {
            "base_url": "https://openrouter.ai/api/v1",
            "api_type": "openai_compatible",
            "models": [
                {
                    "id": "microsoft/phi-3-mini-128k-instruct:free",
                    "name": "Phi-3 Mini 128K (Free)",
                    "max_tokens": 128000,
                    "cost_per_token": 0.0
                },
                {
                    "id": "google/gemma-7b-it:free",
                    "name": "Gemma 7B IT (Free)", 
                    "max_tokens": 8192,
                    "cost_per_token": 0.0
                },
                {
                    "id": "meta-llama/llama-3-8b-instruct:free",
                    "name": "Llama 3 8B Instruct (Free)",
                    "max_tokens": 8192,
                    "cost_per_token": 0.0
                },
                {
                    "id": "mistralai/mistral-7b-instruct:free",
                    "name": "Mistral 7B Instruct (Free)",
                    "max_tokens": 32768,
                    "cost_per_token": 0.0
                },
                {
                    "id": "huggingfaceh4/zephyr-7b-beta:free",
                    "name": "Zephyr 7B Beta (Free)",
                    "max_tokens": 32768,
                    "cost_per_token": 0.0
                }
            ],
            "headers": {
                "HTTP-Referer": "https://duckbot-ai.local",
                "X-Title": "DuckBot AI"
            },
            "authentication": {
                "type": "optional",
                "description": "API key optional for free models"
            }
        }
    }
    
    return tool_config

def create_openwebui_function():
    """Create OpenWebUI function for OpenRouter integration"""
    
    function_code = '''
import json
import requests
from typing import Dict, Any, List
import os

class Pipe:
    """OpenWebUI Pipe for OpenRouter Free Models"""
    
    def __init__(self):
        self.type = "pipe"
        self.id = "openrouter_free"
        self.name = "OpenRouter Free"
        self.version = "1.0.0"
        
    def pipes(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "openrouter_free",
                "name": "OpenRouter Free Models",
                "type": "pipe",
                "description": "Access OpenRouter's free AI models"
            }
        ]
    
    def pipe(self, prompt: str, model_id: str, messages: List[Dict], **kwargs) -> str:
        """Process request through OpenRouter free models"""
        
        # OpenRouter API endpoint
        api_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "HTTP-Referer": "https://duckbot-ai.local",
            "X-Title": "DuckBot AI"
        }
        
        # Add API key if available (optional for free models)
        api_key = os.getenv("OPENROUTER_API_KEY")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        # Prepare payload
        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 4000),
            "stream": False
        }
        
        try:
            # Make API request
            response = requests.post(api_url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                return f"Error: {response.status_code} - {response.text}"
                
        except Exception as e:
            return f"Error: {str(e)}"
    
    def run(self, prompt: str, **kwargs) -> str:
        """Main execution method"""
        model_id = kwargs.get("model", "microsoft/phi-3-mini-128k-instruct:free")
        messages = kwargs.get("messages", [{"role": "user", "content": prompt}])
        
        return self.pipe(prompt, model_id, messages, **kwargs)
'''
    
    return function_code

def main():
    """Create all OpenWebUI plugin files"""
    print("[TOOLS] Creating OpenWebUI plugin for OpenRouter free models...")
    
    # Create plugin directory
    import os
    from pathlib import Path
    
    plugin_dir = Path.cwd() / "openwebui_plugins" / "openrouter_free"
    plugin_dir.mkdir(parents=True, exist_ok=True)
    
    # Create manifest
    manifest = create_openwebui_plugin_manifest()
    with open(plugin_dir / "manifest.json", 'w') as f:
        json.dump(manifest, f, indent=2)
    
    # Create tool config
    tool_config = create_openwebui_tool_config()
    with open(plugin_dir / "tool_config.json", 'w') as f:
        json.dump(tool_config, f, indent=2)
    
    # Create function
    function_code = create_openwebui_function()
    with open(plugin_dir / "openrouter_pipe.py", 'w') as f:
        f.write(function_code)
    
    # Create plugin info
    plugin = OpenRouterFreePlugin()
    plugin_data = plugin.format_for_openwebui()
    with open(plugin_dir / "plugin.json", 'w') as f:
        json.dump(plugin_data, f, indent=2)
    
    # Create README
    readme_content = """# OpenWebUI OpenRouter Free Models Plugin

## Description
This plugin provides access to OpenRouter's free AI models through OpenWebUI.

## Free Models Available:
- microsoft/phi-3-mini-128k-instruct:free
- google/gemma-7b-it:free
- meta-llama/llama-3-8b-instruct:free
- mistralai/mistral-7b-instruct:free
- huggingfaceh4/zephyr-7b-beta:free

## Installation:
1. Copy this folder to your OpenWebUI plugins directory
2. Restart OpenWebUI
3. Enable the plugin in settings
4. Optional: Add OPENROUTER_API_KEY for higher rate limits

## Usage:
- Select any free model from the model dropdown
- Start chatting - no API key required!
- All models are completely FREE through OpenRouter
"""
    
    with open(plugin_dir / "README.md", 'w') as f:
        f.write(readme_content)
    
    print(f"[OK] Plugin created in: {plugin_dir}")
    print("[DIR] Files created:")
    print("   • manifest.json - Plugin manifest")
    print("   • tool_config.json - Tool configuration")  
    print("   • openrouter_pipe.py - OpenWebUI pipe function")
    print("   • plugin.json - Plugin data")
    print("   • README.md - Documentation")
    print("\n[TARGET] To install:")
    print("1. Copy the openrouter_free folder to your OpenWebUI plugins directory")
    print("2. Restart OpenWebUI")
    print("3. Enable the plugin in OpenWebUI settings")

if __name__ == "__main__":
    main()