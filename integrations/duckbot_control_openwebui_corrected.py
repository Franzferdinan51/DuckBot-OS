'''
OpenWebUI Tool for DuckBot AI Chat
==================================

This tool allows you to chat with the DuckBot AI system directly from OpenWebUI.

Usage in OpenWebUI:
1. Import this as a custom tool
2. Use the tool to send messages to DuckBot AI

Author: Gemini
Version: 1.0
'''

import requests
from typing import Optional

class Tools:
    def __init__(self):
        self.duckbot_url = "http://localhost:8787"
        self.token = None
        self.timeout = 60

    def get_duckbot_token(self) -> Optional[str]:
        '''Get DuckBot authentication token'''
        if self.token:
            return self.token
            
        try:
            response = requests.get(f"{self.duckbot_url}/token", timeout=5)
            if response.status_code == 200:
                self.token = response.json().get("token")
                return self.token
        except:
            return None

    def duckbot_ai_chat(self, message: str, task_type: str = "auto") -> str:
        '''
        Chat with DuckBot AI system.
        
        Args:
            message: Your message or question for DuckBot AI
            task_type: Type of AI task - auto, code, reasoning, summary, long_form
        
        Returns:
            AI response from DuckBot
        '''
        
        if not message.strip():
            return "[FAIL] Please provide a message for DuckBot AI"
        
        try:
            token = self.get_duckbot_token()
            if not token:
                return "[FAIL] DuckBot server not available at http://localhost:8787. Make sure DuckBot is running."
            
            headers = {"Authorization": f"Bearer {token}"}
            data = {"message": message, "kind": task_type, "risk": "medium"}
            
            response = requests.post(f"{self.duckbot_url}/chat", headers=headers, data=data, timeout=30)
            
            if response.status_code == 200:
                return response.json().get("response", "[OK] Task completed, but no response content.")
            else:
                return f"[FAIL] Error: {response.status_code} - {response.text}"
        except Exception as e:
            return f"[FAIL] An unexpected error occurred: {e}"

# OpenWebUI Tool Function
def duckbot_chat(message: str, task_type: str = "auto") -> str:
    '''
    Chat with the DuckBot AI system.
    
    Args:
        message: Your message or question for DuckBot AI.
        task_type: The type of AI task to perform (e.g., "auto", "code", "reasoning").
        
    Returns:
        The AI's response.
    '''
    tools = Tools()
    return tools.duckbot_ai_chat(message, task_type)

# Tool metadata for OpenWebUI
TOOL_METADATA = {
    "name": "duckbot_chat",
    "description": "Chat with the DuckBot AI system.",
    "parameters": {
        "message": {
            "type": "string",
            "description": "Your message or question for DuckBot AI.",
            "required": True
        },
        "task_type": {
            "type": "string",
            "description": "The type of AI task to perform (e.g., 'auto', 'code', 'reasoning').",
            "default": "auto",
            "required": False
        }
    }
}
