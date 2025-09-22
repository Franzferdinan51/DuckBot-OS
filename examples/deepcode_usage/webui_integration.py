#!/usr/bin/env python3
"""
DeepCode WebUI Integration Examples

This file demonstrates how to integrate DeepCode with the DuckBot WebUI
for seamless user experience and advanced features.
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Add the DuckBot path to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from launcher_modules.deepcode.deepcode_integration import DuckBotDeepCodeIntegration


class DeepCodeWebUI:
    """WebUI integration class for DeepCode."""

    def __init__(self):
        """Initialize the WebUI integration."""
        self.deepcode = DuckBotDeepCodeIntegration()
        self.active_sessions = {}
        self.websocket_connections = {}

    async def create_session(self, user_id: str, session_config: Dict[str, Any]) -> str:
        """Create a new DeepCode session for a user.

        Args:
            user_id: Unique user identifier
            session_config: Session configuration

        Returns:
            Session ID
        """
        session_id = f"session_{user_id}_{asyncio.get_event_loop().time()}"
        self.active_sessions[session_id] = {
            "user_id": user_id,
            "config": session_config,
            "tasks": [],
            "created_at": asyncio.get_event_loop().time()
        }
        return session_id

    async def submit_task(
        self,
        session_id: str,
        task_type: str,
        content: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Submit a task through the WebUI.

        Args:
            session_id: Session identifier
            task_type: Type of task (paper2code, text2web, text2backend)
            content: Task content/description
            config: Task configuration

        Returns:
            Task submission result
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Invalid session ID: {session_id}")

        session = self.active_sessions[session_id]

        # Apply session configuration
        task_config = {**session["config"], **(config or {})}

        try:
            if task_type == "paper2code":
                result = await self.deepcode.paper2code(
                    paper_description=content,
                    config=task_config
                )
            elif task_type == "text2web":
                result = await self.deepcode.text2web(
                    description=content,
                    config=task_config
                )
            elif task_type == "text2backend":
                result = await self.deepcode.text2backend(
                    description=content,
                    config=task_config
                )
            else:
                raise ValueError(f"Unsupported task type: {task_type}")

            # Add task to session
            session["tasks"].append({
                "task_id": result["task_id"],
                "type": task_type,
                "status": result["status"],
                "submitted_at": asyncio.get_event_loop().time()
            })

            return result

        except Exception as e:
            return {
                "error": str(e),
                "task_type": task_type,
                "status": "failed"
            }

    async def get_task_progress(self, session_id: str, task_id: str) -> Dict[str, Any]:
        """Get task progress for WebUI display.

        Args:
            session_id: Session identifier
            task_id: Task identifier

        Returns:
            Task progress information
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Invalid session ID: {session_id}")

        try:
            status = await self.deepcode.get_task_status(task_id)
            return {
                "task_id": task_id,
                "progress": status.get("progress", 0),
                "status": status["status"],
                "current_step": status.get("current_step", ""),
                "message": status.get("message", ""),
                "generated_files": status.get("generated_files", []),
                "error": status.get("error", None)
            }
        except Exception as e:
            return {
                "task_id": task_id,
                "progress": 0,
                "status": "error",
                "message": str(e),
                "error": str(e)
            }

    async def get_session_tasks(self, session_id: str) -> list:
        """Get all tasks for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of tasks in the session
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Invalid session ID: {session_id}")

        session = self.active_sessions[session_id]
        tasks = []

        for task_info in session["tasks"]:
            try:
                status = await self.deepcode.get_task_status(task_info["task_id"])
                task_info.update({
                    "progress": status.get("progress", 0),
                    "current_step": status.get("current_step", ""),
                    "message": status.get("message", ""),
                    "generated_files": status.get("generated_files", []),
                    "error": status.get("error", None)
                })
            except Exception as e:
                task_info.update({
                    "progress": 0,
                    "status": "error",
                    "message": str(e),
                    "error": str(e)
                })

            tasks.append(task_info)

        return tasks

    async def cancel_task(self, session_id: str, task_id: str) -> Dict[str, Any]:
        """Cancel a running task.

        Args:
            session_id: Session identifier
            task_id: Task identifier

        Returns:
            Cancellation result
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Invalid session ID: {session_id}")

        # This would need to be implemented in the DeepCode integration
        # For now, return mock response
        return {
            "task_id": task_id,
            "cancelled": True,
            "message": "Task cancelled successfully"
        }

    async def get_file_preview(self, session_id: str, task_id: str, file_path: str) -> str:
        """Get preview of a generated file.

        Args:
            session_id: Session identifier
            task_id: Task identifier
            file_path: Path to the file

        Returns:
            File content preview
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Invalid session ID: {session_id}")

        try:
            # This would need to be implemented in the DeepCode integration
            # For now, return mock content
            return f"Preview of {file_path} from task {task_id}"
        except Exception as e:
            return f"Error getting file preview: {str(e)}"

    async def download_project(self, session_id: str, task_id: str) -> Dict[str, Any]:
        """Download generated project as zip file.

        Args:
            session_id: Session identifier
            task_id: Task identifier

        Returns:
            Download information
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Invalid session ID: {session_id}")

        try:
            # This would need to be implemented in the DeepCode integration
            # For now, return mock response
            return {
                "task_id": task_id,
                "download_url": f"/api/download/{task_id}",
                "file_name": f"project_{task_id}.zip",
                "file_size": 1024000,
                "created_at": asyncio.get_event_loop().time()
            }
        except Exception as e:
            return {
                "task_id": task_id,
                "error": str(e)
            }

    async def get_user_templates(self, user_id: str) -> list:
        """Get user's custom templates.

        Args:
            user_id: User identifier

        Returns:
            List of user templates
        """
        # This would query a database for user templates
        # For now, return mock templates
        return [
            {
                "id": "template_1",
                "name": "My ML Template",
                "description": "Custom machine learning template",
                "created_at": "2024-01-01T00:00:00Z",
                "last_used": "2024-01-15T00:00:00Z"
            },
            {
                "id": "template_2",
                "name": "API Template",
                "description": "REST API template with authentication",
                "created_at": "2024-01-02T00:00:00Z",
                "last_used": "2024-01-14T00:00:00Z"
            }
        ]

    async def save_template(self, user_id: str, template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save a custom template for a user.

        Args:
            user_id: User identifier
            template_data: Template configuration

        Returns:
            Template save result
        """
        # This would save to a database
        # For now, return mock response
        template_id = f"template_{user_id}_{asyncio.get_event_loop().time()}"
        return {
            "template_id": template_id,
            "name": template_data.get("name", "Untitled Template"),
            "created_at": asyncio.get_event_loop().time(),
            "message": "Template saved successfully"
        }

    async def get_task_history(self, user_id: str, limit: int = 50) -> list:
        """Get user's task history.

        Args:
            user_id: User identifier
            limit: Maximum number of tasks to return

        Returns:
            List of historical tasks
        """
        # This would query a database for user history
        # For now, return mock history
        return [
            {
                "task_id": "task_1",
                "type": "paper2code",
                "status": "completed",
                "created_at": "2024-01-15T10:00:00Z",
                "completed_at": "2024-01-15T10:15:00Z",
                "duration": 900,
                "description": "Research paper on neural networks"
            },
            {
                "task_id": "task_2",
                "type": "text2web",
                "status": "completed",
                "created_at": "2024-01-14T14:00:00Z",
                "completed_at": "2024-01-14T14:30:00Z",
                "duration": 1800,
                "description": "E-commerce product catalog"
            }
        ]

    async def get_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get user statistics.

        Args:
            user_id: User identifier

        Returns:
            User statistics
        """
        # This would calculate real statistics
        # For now, return mock statistics
        return {
            "total_tasks": 25,
            "completed_tasks": 20,
            "failed_tasks": 2,
            "active_tasks": 3,
            "total_files_generated": 1250,
            "total_code_lines": 45600,
            "average_task_duration": 1200,
            "most_used_framework": "react",
            "most_used_language": "python",
            "success_rate": 0.8,
            "favorite_task_type": "text2web"
        }


# WebSocket event handlers
async def handle_websocket_connect(websocket, session_id: str):
    """Handle WebSocket connection."""
    webui = DeepCodeWebUI()
    webui.websocket_connections[session_id] = websocket

    try:
        async for message in websocket:
            data = json.loads(message)
            await handle_websocket_message(webui, websocket, session_id, data)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        if session_id in webui.websocket_connections:
            del webui.websocket_connections[session_id]


async def handle_websocket_message(webui, websocket, session_id: str, data: Dict[str, Any]):
    """Handle WebSocket messages."""
    message_type = data.get("type")

    if message_type == "submit_task":
        result = await webui.submit_task(
            session_id,
            data["task_type"],
            data["content"],
            data.get("config", {})
        )
        await websocket.send(json.dumps({
            "type": "task_submitted",
            "data": result
        }))

    elif message_type == "get_progress":
        progress = await webui.get_task_progress(session_id, data["task_id"])
        await websocket.send(json.dumps({
            "type": "task_progress",
            "data": progress
        }))

    elif message_type == "cancel_task":
        result = await webui.cancel_task(session_id, data["task_id"])
        await websocket.send(json.dumps({
            "type": "task_cancelled",
            "data": result
        }))

    elif message_type == "get_session_tasks":
        tasks = await webui.get_session_tasks(session_id)
        await websocket.send(json.dumps({
            "type": "session_tasks",
            "data": tasks
        }))


# REST API endpoints for WebUI
async def webui_submit_task(request):
    """REST API endpoint for task submission."""
    data = await request.json()
    session_id = data.get("session_id")
    task_type = data.get("task_type")
    content = data.get("content")
    config = data.get("config", {})

    webui = DeepCodeWebUI()
    result = await webui.submit_task(session_id, task_type, content, config)

    return {
        "success": True,
        "data": result
    }


async def webui_get_task_status(request):
    """REST API endpoint for task status."""
    session_id = request.query.get("session_id")
    task_id = request.query.get("task_id")

    webui = DeepCodeWebUI()
    progress = await webui.get_task_progress(session_id, task_id)

    return {
        "success": True,
        "data": progress
    }


async def webui_get_session(request):
    """REST API endpoint for session data."""
    session_id = request.query.get("session_id")

    webui = DeepCodeWebUI()
    tasks = await webui.get_session_tasks(session_id)

    return {
        "success": True,
        "data": {
            "session_id": session_id,
            "tasks": tasks
        }
    }


# Example usage
async def webui_example():
    """Example of WebUI integration."""
    print("=== WebUI Integration Example ===")

    webui = DeepCodeWebUI()

    # Create a session
    user_id = "user_123"
    session_config = {
        "model": "qwen3-coder",
        "temperature": 0.2,
        "include_tests": True,
        "include_documentation": True
    }

    session_id = await webui.create_session(user_id, session_config)
    print(f"Created session: {session_id}")

    # Submit a task
    paper_content = """
    This paper presents a novel approach to sentiment analysis using transformer models.
    The model achieves state-of-the-art performance on multiple benchmarks.
    """

    result = await webui.submit_task(
        session_id,
        "paper2code",
        paper_content,
        {"include_tests": True}
    )

    print(f"Submitted task: {result['task_id']}")

    # Monitor progress
    while True:
        progress = await webui.get_task_progress(session_id, result['task_id'])
        print(f"Progress: {progress['progress']}% - {progress.get('current_step', '')}")

        if progress['status'] in ['completed', 'failed']:
            break

        await asyncio.sleep(2)

    # Get session tasks
    tasks = await webui.get_session_tasks(session_id)
    print(f"Session tasks: {len(tasks)}")

    # Get user statistics
    stats = await webui.get_statistics(user_id)
    print(f"User statistics: {stats}")


if __name__ == "__main__":
    asyncio.run(webui_example())