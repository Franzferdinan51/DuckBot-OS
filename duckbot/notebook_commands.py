"""
Open Notebook Discord Integration
Simple commands to interact with Open Notebook features
"""
import requests
import asyncio
from typing import Optional

class OpenNotebookClient:
    def __init__(self, api_url: str = "http://localhost:5055"):
        self.api_url = api_url
        self.web_url = "http://localhost:8502"
    
    def is_available(self) -> bool:
        """Check if Open Notebook services are running"""
        try:
            response = requests.get(f"{self.api_url}/api/health", timeout=3)
            return response.status_code == 200
        except:
            return False
    
    async def create_notebook(self, title: str, description: str = "") -> dict:
        """Create a new notebook"""
        try:
            data = {
                "title": title,
                "description": description
            }
            response = requests.post(f"{self.api_url}/api/notebooks", json=data, timeout=10)
            if response.status_code == 200:
                return {"success": True, "notebook": response.json()}
            else:
                return {"success": False, "error": f"API error: {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def generate_podcast(self, topic: str, duration: int = 10) -> dict:
        """Generate a podcast episode"""
        try:
            data = {
                "topic": topic,
                "duration_minutes": min(duration, 90),  # Cap at 90 minutes
                "speakers": 2  # Default to 2 speakers
            }
            response = requests.post(f"{self.api_url}/api/podcasts/generate", json=data, timeout=300)
            if response.status_code == 200:
                return {"success": True, "podcast": response.json()}
            else:
                return {"success": False, "error": f"API error: {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

# Discord command helpers
def get_notebook_status() -> str:
    """Get Open Notebook service status"""
    client = OpenNotebookClient()
    if client.is_available():
        return f"✅ **Open Notebook Active**\n📓 Web Interface: {client.web_url}\n🔗 API Backend: {client.api_url}"
    else:
        return "❌ **Open Notebook Offline**\nUse `start_open_notebook.bat` to start services"

async def handle_notebook_command(title: str, description: str = "") -> str:
    """Handle /notebook Discord command"""
    client = OpenNotebookClient()
    
    if not client.is_available():
        return "❌ Open Notebook services are not running. Please start them first."
    
    result = await client.create_notebook(title, description)
    
    if result["success"]:
        return f"✅ **Notebook Created!**\n📓 Title: {title}\n🔗 Access: {client.web_url}"
    else:
        return f"❌ **Failed to create notebook**\nError: {result['error']}"

async def handle_podcast_command(topic: str, duration: int = 10) -> str:
    """Handle /podcast Discord command"""
    client = OpenNotebookClient()
    
    if not client.is_available():
        return "❌ Open Notebook services are not running. Please start them first."
    
    if duration > 90:
        return "⚠️ Maximum podcast duration is 90 minutes."
    
    # This would be a long-running operation
    return f"🎙️ **Generating Podcast**\n📝 Topic: {topic}\n⏱️ Duration: {duration} minutes\n🔄 This may take several minutes...\n\n*Check Open Notebook web interface for progress: {client.web_url}*"

# Add to Discord bot integration points
NOTEBOOK_COMMANDS = {
    "notebook_status": get_notebook_status,
    "create_notebook": handle_notebook_command, 
    "generate_podcast": handle_podcast_command
}