#!/usr/bin/env python3
"""
PyBoy WebUI Interface for DuckBot
Provides web interface for Game Boy emulator functionality
"""

import asyncio
import json
import base64
import io
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class PyBoyWebUI:
    """WebUI interface for PyBoy integration"""

    def __init__(self, pyboy_integration):
        self.pyboy = pyboy_integration
        self.game_sessions = {}
        self.current_session_id = None

    async def get_game_info(self) -> Dict[str, Any]:
        """Get current game information"""
        try:
            return await self.pyboy.get_game_info()
        except Exception as e:
            logger.error(f"Failed to get game info: {e}")
            return {}

    async def get_available_roms(self) -> List[str]:
        """Get list of available ROM files"""
        try:
            return await self.pyboy.get_available_roms()
        except Exception as e:
            logger.error(f"Failed to get ROMs: {e}")
            return []

    async def load_game(self, rom_name: str) -> Dict[str, Any]:
        """Load a game"""
        try:
            rom_path = f"roms/{rom_name}"
            success = await self.pyboy.load_game(rom_path)

            if success:
                # Create game session
                session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                self.game_sessions[session_id] = {
                    "rom_name": rom_name,
                    "rom_path": rom_path,
                    "start_time": datetime.now().isoformat(),
                    "frame_count": 0,
                    "actions_taken": 0
                }
                self.current_session_id = session_id

                return {
                    "success": True,
                    "session_id": session_id,
                    "message": f"Game {rom_name} loaded successfully"
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to load game {rom_name}"
                }

        except Exception as e:
            logger.error(f"Failed to load game {rom_name}: {e}")
            return {
                "success": False,
                "message": f"Error loading game: {str(e)}"
            }

    async def stop_game(self) -> Dict[str, Any]:
        """Stop current game"""
        try:
            await self.pyboy.stop_game()
            self.current_session_id = None
            return {
                "success": True,
                "message": "Game stopped successfully"
            }
        except Exception as e:
            logger.error(f"Failed to stop game: {e}")
            return {
                "success": False,
                "message": f"Error stopping game: {str(e)}"
            }

    async def get_frame(self) -> Dict[str, Any]:
        """Get current game frame as base64 image"""
        try:
            frame = await self.pyboy.get_frame()
            if frame is not None:
                # Convert numpy array to base64
                import numpy as np
                from PIL import Image

                # Convert grayscale to RGB if needed
                if len(frame.shape) == 2:
                    frame = np.stack([frame] * 3, axis=-1)

                # Convert to PIL Image and then to base64
                img = Image.fromarray(frame.astype(np.uint8))
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                img_base64 = base64.b64encode(buffer.getvalue()).decode()

                return {
                    "success": True,
                    "frame": img_base64,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "message": "No frame available"
                }

        except Exception as e:
            logger.error(f"Failed to get frame: {e}")
            return {
                "success": False,
                "message": f"Error getting frame: {str(e)}"
            }

    async def press_button(self, button: str) -> Dict[str, Any]:
        """Press a game button"""
        try:
            success = await self.pyboy.press_button(button)

            # Update session stats
            if success and self.current_session_id:
                session = self.game_sessions.get(self.current_session_id)
                if session:
                    session["actions_taken"] += 1

            return {
                "success": success,
                "button": button,
                "message": f"Button {button} pressed" if success else f"Failed to press {button}"
            }

        except Exception as e:
            logger.error(f"Failed to press button {button}: {e}")
            return {
                "success": False,
                "button": button,
                "message": f"Error pressing button: {str(e)}"
            }

    async def run_ai_agent(self, agent_type: str = "random", max_frames: int = 100) -> Dict[str, Any]:
        """Run AI agent to play the game"""
        try:
            if agent_type == "random":
                from duckbot.integrations.pyboy_integration import RandomAIAgent
                agent = RandomAIAgent(self.pyboy)
            else:
                return {
                    "success": False,
                    "message": f"Unknown agent type: {agent_type}"
                }

            results = await self.pyboy.run_ai_agent(
                agent_func=agent.decide_action,
                max_frames=max_frames
            )

            # Update session stats
            if self.current_session_id and results.get("success"):
                session = self.game_sessions.get(self.current_session_id)
                if session:
                    session["frames_processed"] = results.get("frames_processed", 0)
                    session["ai_actions_taken"] = results.get("actions_taken", 0)

            return {
                "success": True,
                "results": results,
                "message": f"AI agent {agent_type} completed"
            }

        except Exception as e:
            logger.error(f"Failed to run AI agent: {e}")
            return {
                "success": False,
                "message": f"Error running AI agent: {str(e)}"
            }

    async def save_game(self, filename: str) -> Dict[str, Any]:
        """Save game state"""
        try:
            success = await self.pyboy.save_state(filename)
            return {
                "success": success,
                "filename": filename,
                "message": f"Game saved as {filename}" if success else f"Failed to save game"
            }

        except Exception as e:
            logger.error(f"Failed to save game: {e}")
            return {
                "success": False,
                "filename": filename,
                "message": f"Error saving game: {str(e)}"
            }

    async def load_game_state(self, filename: str) -> Dict[str, Any]:
        """Load game state"""
        try:
            success = await self.pyboy.load_state(filename)
            return {
                "success": success,
                "filename": filename,
                "message": f"Game state {filename} loaded" if success else f"Failed to load {filename}"
            }

        except Exception as e:
            logger.error(f"Failed to load game state: {e}")
            return {
                "success": False,
                "filename": filename,
                "message": f"Error loading game state: {str(e)}"
            }

    async def get_sessions(self) -> List[Dict[str, Any]]:
        """Get list of game sessions"""
        return [
            {
                "session_id": session_id,
                "rom_name": session["rom_name"],
                "start_time": session["start_time"],
                "frame_count": session.get("frame_count", 0),
                "actions_taken": session.get("actions_taken", 0),
                "is_current": session_id == self.current_session_id
            }
            for session_id, session in self.game_sessions.items()
        ]

    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        try:
            game_info = await self.pyboy.get_game_info()
            performance = game_info.get("performance", {})

            return {
                "fps": performance.get("fps", 0),
                "frames_processed": performance.get("frames_processed", 0),
                "actions_taken": performance.get("actions_taken", 0),
                "uptime_seconds": performance.get("uptime_seconds", 0),
                "ai_enabled": performance.get("ai_enabled", False)
            }
        except Exception as e:
            logger.error(f"Failed to get performance stats: {e}")
            return {}

    async def run_frame(self) -> Dict[str, Any]:
        """Run a single frame"""
        try:
            success = await self.pyboy.run_frame()

            # Update session stats
            if success and self.current_session_id:
                session = self.game_sessions.get(self.current_session_id)
                if session:
                    session["frame_count"] = session.get("frame_count", 0) + 1

            return {
                "success": success,
                "message": "Frame processed successfully" if success else "Failed to process frame"
            }

        except Exception as e:
            logger.error(f"Failed to run frame: {e}")
            return {
                "success": False,
                "message": f"Error running frame: {str(e)}"
            }

    async def get_game_controls(self) -> Dict[str, Any]:
        """Get available game controls"""
        return {
            "buttons": [
                {"name": "up", "label": "↑ Up", "key": "ArrowUp"},
                {"name": "down", "label": "↓ Down", "key": "ArrowDown"},
                {"name": "left", "label": "← Left", "key": "ArrowLeft"},
                {"name": "right", "label": "→ Right", "key": "ArrowRight"},
                {"name": "a", "label": "A Button", "key": "z"},
                {"name": "b", "label": "B Button", "key": "x"},
                {"name": "start", "label": "Start", "key": "Enter"},
                {"name": "select", "label": "Select", "key": "Shift"}
            ],
            "ai_agents": [
                {"name": "random", "label": "Random Agent", "description": "Makes random button presses"},
                {"name": "smart", "label": "Smart Agent", "description": "AI-powered gameplay (future)"}
            ]
        }

    async def cleanup(self):
        """Clean up resources"""
        try:
            await self.pyboy.cleanup()
            self.game_sessions.clear()
            self.current_session_id = None
            logger.info("PyBoy WebUI interface cleaned up")
        except Exception as e:
            logger.error(f"Failed to cleanup PyBoy WebUI: {e}")


# Flask/DuckBot WebUI integration functions
def create_pyboy_routes(app, pyboy_integration):
    """Create Flask routes for PyBoy WebUI"""

    # Initialize WebUI interface
    pyboy_webui = PyBoyWebUI(pyboy_integration)

    @app.route('/api/pyboy/info', methods=['GET'])
    async def get_pyboy_info():
        """Get PyBoy system information"""
        try:
            info = await pyboy_webui.get_game_info()
            return {
                "success": True,
                "data": info
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }, 500

    @app.route('/api/pyboy/roms', methods=['GET'])
    async def get_available_roms():
        """Get available ROM files"""
        try:
            roms = await pyboy_webui.get_available_roms()
            return {
                "success": True,
                "data": roms
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }, 500

    @app.route('/api/pyboy/load', methods=['POST'])
    async def load_game():
        """Load a game"""
        try:
            data = await request.get_json()
            rom_name = data.get('rom_name')

            if not rom_name:
                return {
                    "success": False,
                    "error": "ROM name is required"
                }, 400

            result = await pyboy_webui.load_game(rom_name)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }, 500

    @app.route('/api/pyboy/stop', methods=['POST'])
    async def stop_game():
        """Stop current game"""
        try:
            result = await pyboy_webui.stop_game()
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }, 500

    @app.route('/api/pyboy/frame', methods=['GET'])
    async def get_frame():
        """Get current game frame"""
        try:
            result = await pyboy_webui.get_frame()
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }, 500

    @app.route('/api/pyboy/control', methods=['POST'])
    async def press_button():
        """Press a game button"""
        try:
            data = await request.get_json()
            button = data.get('button')

            if not button:
                return {
                    "success": False,
                    "error": "Button is required"
                }, 400

            result = await pyboy_webui.press_button(button)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }, 500

    @app.route('/api/pyboy/ai', methods=['POST'])
    async def run_ai_agent():
        """Run AI agent"""
        try:
            data = await request.get_json()
            agent_type = data.get('agent_type', 'random')
            max_frames = data.get('max_frames', 100)

            result = await pyboy_webui.run_ai_agent(agent_type, max_frames)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }, 500

    @app.route('/api/pyboy/save', methods=['POST'])
    async def save_game():
        """Save game state"""
        try:
            data = await request.get_json()
            filename = data.get('filename')

            if not filename:
                return {
                    "success": False,
                    "error": "Filename is required"
                }, 400

            result = await pyboy_webui.save_game(filename)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }, 500

    @app.route('/api/pyboy/load_state', methods=['POST'])
    async def load_game_state():
        """Load game state"""
        try:
            data = await request.get_json()
            filename = data.get('filename')

            if not filename:
                return {
                    "success": False,
                    "error": "Filename is required"
                }, 400

            result = await pyboy_webui.load_game_state(filename)
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }, 500

    @app.route('/api/pyboy/sessions', methods=['GET'])
    async def get_sessions():
        """Get game sessions"""
        try:
            sessions = await pyboy_webui.get_sessions()
            return {
                "success": True,
                "data": sessions
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }, 500

    @app.route('/api/pyboy/performance', methods=['GET'])
    async def get_performance():
        """Get performance statistics"""
        try:
            stats = await pyboy_webui.get_performance_stats()
            return {
                "success": True,
                "data": stats
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }, 500

    @app.route('/api/pyboy/controls', methods=['GET'])
    async def get_controls():
        """Get game controls"""
        try:
            controls = await pyboy_webui.get_game_controls()
            return {
                "success": True,
                "data": controls
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }, 500

    @app.route('/api/pyboy/run_frame', methods=['POST'])
    async def run_frame():
        """Run a single frame"""
        try:
            result = await pyboy_webui.run_frame()
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }, 500

    logger.info("PyBoy WebUI routes registered")

    return pyboy_webui