#!/usr/bin/env python3
"""
PyBoy Integration for DuckBot
Game Boy emulator with AI/automation capabilities
"""

import os
import asyncio
import logging
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import json
from datetime import datetime

try:
    import pyboy
    from pyboy import PyBoy
    from pyboy.utils import WindowEvent
    PYBOY_AVAILABLE = True
except ImportError as e:
    print(f"PyBoy import error: {e}")
    PYBOY_AVAILABLE = False
    PyBoy = None
    WindowEvent = None

# Configure logging
logger = logging.getLogger(__name__)

class PyBoyIntegration:
    """PyBoy Game Boy emulator integration for DuckBot"""

    def __init__(self, headless: bool = False):
        self.pyboy = None
        self.current_rom = None
        self.is_running = False
        self.headless = headless
        self.game_state = {}
        self.ai_enabled = False
        self.frame_count = 0
        self.last_action = None
        self.performance_stats = {
            "fps": 0,
            "frames_processed": 0,
            "actions_taken": 0,
            "start_time": None
        }

    def is_available(self) -> bool:
        """Check if PyBoy is available"""
        return PYBOY_AVAILABLE

    async def initialize(self) -> bool:
        """Initialize PyBoy integration"""
        if not self.is_available():
            logger.error("PyBoy is not available. Install with: pip install pyboy")
            return False

        try:
            logger.info("PyBoy integration initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize PyBoy: {e}")
            return False

    async def load_game(self, rom_path: str) -> bool:
        """Load a Game Boy ROM"""
        if not self.is_available():
            logger.error("PyBoy not available")
            return False

        try:
            # Check if ROM file exists
            if not os.path.exists(rom_path):
                logger.error(f"ROM file not found: {rom_path}")
                return False

            # Stop current game if running
            if self.pyboy:
                await self.stop_game()

            # Initialize PyBoy
            window_type = "headless" if self.headless else "SDL2"
            self.pyboy = PyBoy(rom_path, window_type=window_type)
            self.current_rom = rom_path
            self.is_running = True
            self.frame_count = 0
            self.performance_stats["start_time"] = datetime.now()

            logger.info(f"Loaded game: {rom_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to load game {rom_path}: {e}")
            return False

    async def stop_game(self):
        """Stop the current game"""
        if self.pyboy:
            try:
                self.pyboy.stop(save=False)
                self.pyboy = None
                self.is_running = False
                self.current_rom = None
                logger.info("Game stopped")
            except Exception as e:
                logger.error(f"Error stopping game: {e}")

    async def get_frame(self) -> Optional[np.ndarray]:
        """Get current game frame as numpy array"""
        if not self.pyboy or not self.is_running:
            return None

        try:
            return self.pyboy.screen.ndarray.copy()
        except Exception as e:
            logger.error(f"Failed to get frame: {e}")
            return None

    async def get_game_info(self) -> Dict[str, Any]:
        """Get current game information"""
        if not self.pyboy or not self.is_running:
            return {}

        try:
            info = {
                "rom_path": self.current_rom,
                "frame_count": self.frame_count,
                "is_running": self.is_running,
                "ai_enabled": self.ai_enabled,
                "fps": self.performance_stats["fps"],
                "last_action": self.last_action,
                "performance": self.performance_stats
            }

            # Add tilemap info if available
            try:
                if hasattr(self.pyboy, 'tilemap'):
                    tilemap = self.pyboy.tilemap
                    info["tilemap"] = {
                        "width": tilemap.width(),
                        "height": tilemap.height(),
                        "tile_count": len(tilemap)
                    }
            except:
                pass

            return info

        except Exception as e:
            logger.error(f"Failed to get game info: {e}")
            return {}

    async def press_button(self, button: str) -> bool:
        """Press a Game Boy button"""
        if not self.pyboy or not self.is_running:
            return False

        button_map = {
            "up": WindowEvent.PRESS_ARROW_UP,
            "down": WindowEvent.PRESS_ARROW_DOWN,
            "left": WindowEvent.PRESS_ARROW_LEFT,
            "right": WindowEvent.PRESS_ARROW_RIGHT,
            "a": WindowEvent.PRESS_BUTTON_A,
            "b": WindowEvent.PRESS_BUTTON_B,
            "start": WindowEvent.PRESS_BUTTON_START,
            "select": WindowEvent.PRESS_BUTTON_SELECT,
        }

        release_map = {
            "up": WindowEvent.RELEASE_ARROW_UP,
            "down": WindowEvent.RELEASE_ARROW_DOWN,
            "left": WindowEvent.RELEASE_ARROW_LEFT,
            "right": WindowEvent.RELEASE_ARROW_RIGHT,
            "a": WindowEvent.RELEASE_BUTTON_A,
            "b": WindowEvent.RELEASE_BUTTON_B,
            "start": WindowEvent.RELEASE_BUTTON_START,
            "select": WindowEvent.RELEASE_BUTTON_SELECT,
        }

        try:
            if button in button_map:
                # Press and release the button
                self.pyboy.send_input(button_map[button])
                await asyncio.sleep(0.05)  # Small delay
                self.pyboy.send_input(release_map[button])

                self.last_action = button
                self.performance_stats["actions_taken"] += 1
                logger.debug(f"Pressed button: {button}")
                return True
            else:
                logger.warning(f"Unknown button: {button}")
                return False

        except Exception as e:
            logger.error(f"Failed to press button {button}: {e}")
            return False

    async def run_frame(self) -> bool:
        """Run a single frame"""
        if not self.pyboy or not self.is_running:
            return False

        try:
            # Run one frame
            self.pyboy.tick()
            self.frame_count += 1
            self.performance_stats["frames_processed"] += 1

            # Calculate FPS
            if self.performance_stats["start_time"]:
                elapsed = (datetime.now() - self.performance_stats["start_time"]).total_seconds()
                if elapsed > 0:
                    self.performance_stats["fps"] = self.frame_count / elapsed

            return True

        except Exception as e:
            logger.error(f"Failed to run frame: {e}")
            return False

    async def run_ai_agent(self, agent_func=None, max_frames: int = 1000) -> Dict[str, Any]:
        """Run AI agent to play the game"""
        if not self.pyboy or not self.is_running:
            return {"success": False, "error": "No game running"}

        try:
            self.ai_enabled = True
            results = {
                "frames_processed": 0,
                "actions_taken": 0,
                "score": 0,
                "success": True,
                "ai_decisions": []
            }

            logger.info("Starting AI agent...")
            start_time = datetime.now()

            for frame in range(max_frames):
                if not self.is_running:
                    break

                # Get current frame for AI analysis
                current_frame = await self.get_frame()

                # AI decision making
                if agent_func:
                    # Use custom AI function
                    action = await agent_func(current_frame, self.game_state)
                else:
                    # Use simple random AI
                    action = await self._simple_ai_agent(current_frame, self.game_state)

                # Execute AI decision
                if action and action != "none":
                    success = await self.press_button(action)
                    if success:
                        results["actions_taken"] += 1
                        results["ai_decisions"].append({
                            "frame": frame,
                            "action": action
                        })

                # Run the frame
                await self.run_frame()
                results["frames_processed"] = frame + 1

                # Update game state
                await self._update_game_state()

                # Check if game is over (simplified)
                if await self._check_game_over():
                    break

            elapsed = (datetime.now() - start_time).total_seconds()
            results["elapsed_time"] = elapsed
            results["fps"] = results["frames_processed"] / elapsed if elapsed > 0 else 0

            logger.info(f"AI agent completed: {results}")
            return results

        except Exception as e:
            logger.error(f"AI agent failed: {e}")
            return {"success": False, "error": str(e)}

        finally:
            self.ai_enabled = False

    async def _simple_ai_agent(self, frame: np.ndarray, game_state: Dict) -> str:
        """Simple AI agent that makes random decisions"""
        import random

        # Simple random action with some bias towards right movement
        actions = ["right", "left", "up", "down", "a", "b", "none"]
        weights = [0.3, 0.2, 0.1, 0.1, 0.15, 0.15, 0.1]

        return random.choices(actions, weights=weights)[0]

    async def _update_game_state(self):
        """Update internal game state"""
        try:
            # This is a simplified version - in a real implementation,
            # you would extract meaningful game state from memory
            self.game_state.update({
                "frame_count": self.frame_count,
                "last_update": datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Failed to update game state: {e}")

    async def _check_game_over(self) -> bool:
        """Check if game is over (simplified)"""
        # This is a placeholder - in a real implementation,
        # you would check game-specific conditions
        return False

    async def save_state(self, filename: str) -> bool:
        """Save game state"""
        if not self.pyboy or not self.is_running:
            return False

        try:
            # Create saves directory if it doesn't exist
            saves_dir = Path("saves")
            saves_dir.mkdir(exist_ok=True)

            save_path = saves_dir / filename
            self.pyboy.save_state(str(save_path))
            logger.info(f"Game state saved to: {save_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            return False

    async def load_state(self, filename: str) -> bool:
        """Load game state"""
        if not self.pyboy or not self.is_running:
            return False

        try:
            save_path = Path("saves") / filename
            if save_path.exists():
                self.pyboy.load_state(str(save_path))
                logger.info(f"Game state loaded from: {save_path}")
                return True
            else:
                logger.error(f"Save file not found: {save_path}")
                return False
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            return False

    async def get_available_roms(self) -> List[str]:
        """Get list of available ROM files"""
        roms_dir = Path("roms")
        if not roms_dir.exists():
            return []

        rom_extensions = [".gb", ".gbc", ".rom"]
        roms = []

        for ext in rom_extensions:
            roms.extend(roms_dir.glob(f"*{ext}"))

        return [str(rom.name) for rom in roms]

    async def cleanup(self):
        """Clean up resources"""
        await self.stop_game()
        logger.info("PyBoy integration cleaned up")


# AI Agent Classes
class GameBoyAIAgent:
    """Base class for Game Boy AI agents"""

    def __init__(self, pyboy_integration: PyBoyIntegration):
        self.pyboy = pyboy_integration
        self.name = "GameBoyAIAgent"
        self.description = "Base Game Boy AI Agent"

    async def decide_action(self, frame: np.ndarray, game_state: Dict) -> str:
        """Decide next action based on game state"""
        raise NotImplementedError

    async def analyze_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """Analyze current frame and extract features"""
        if frame is None:
            return {}

        try:
            return {
                "frame_shape": frame.shape,
                "frame_mean": float(np.mean(frame)),
                "frame_std": float(np.std(frame)),
                "frame_max": float(np.max(frame)),
                "frame_min": float(np.min(frame))
            }
        except Exception as e:
            logger.error(f"Frame analysis failed: {e}")
            return {}


class RandomAIAgent(GameBoyAIAgent):
    """Random action AI agent for testing"""

    def __init__(self, pyboy_integration: PyBoyIntegration):
        super().__init__(pyboy_integration)
        self.name = "RandomAIAgent"
        self.description = "Random action AI agent for testing"
        self.actions = ["up", "down", "left", "right", "a", "b", "start", "select", "none"]

    async def decide_action(self, frame: np.ndarray, game_state: Dict) -> str:
        import random
        return random.choice(self.actions)


# Helper function to create and initialize PyBoy integration
async def create_pyboy_integration(headless: bool = True) -> Optional[PyBoyIntegration]:
    """Create and initialize PyBoy integration"""
    integration = PyBoyIntegration(headless=headless)

    if await integration.initialize():
        return integration
    else:
        logger.error("Failed to initialize PyBoy integration")
        return None


# Example usage functions
async def example_pyboy_usage():
    """Example of how to use PyBoy integration"""

    # Create integration
    pyboy = await create_pyboy_integration(headless=True)
    if not pyboy:
        print("Failed to create PyBoy integration")
        return

    try:
        # List available ROMs
        roms = await pyboy.get_available_roms()
        print(f"Available ROMs: {roms}")

        if roms:
            # Load first ROM
            rom_path = f"roms/{roms[0]}"
            if await pyboy.load_game(rom_path):
                print(f"Loaded game: {rom_path}")

                # Run simple AI agent
                results = await pyboy.run_ai_agent(max_frames=100)
                print(f"AI results: {results}")

                # Get game info
                info = await pyboy.get_game_info()
                print(f"Game info: {info}")

    finally:
        await pyboy.cleanup()


if __name__ == "__main__":
    # Test the integration
    asyncio.run(example_pyboy_usage())