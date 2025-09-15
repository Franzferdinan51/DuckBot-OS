#!/usr/bin/env python3
"""
Handcrafted Persona Engine Integration for DuckBot
Integrates Franzferdinan51/handcrafted-persona-engine for advanced character animation and voice synthesis
"""

import os
import json
import logging
import asyncio
import subprocess
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

try:
    # Placeholder for future integration with Handcrafted Persona Engine
    PERSONA_ENGINE_AVAILABLE = True
except ImportError:
    PERSONA_ENGINE_AVAILABLE = False
    logger.warning("Handcrafted Persona Engine not available")

@dataclass
class PersonaEngineConfig:
    """Configuration for Handcrafted Persona Engine integration"""
    host: str = "127.0.0.1"
    port: int = 8788  # Default Persona Engine port
    base_url: str = "http://127.0.0.1:8788"
    api_key: Optional[str] = None
    timeout: int = 30
    character_model: str = "aria"  # Default character
    voice_model: str = "default"   # Default voice
    enable_animation: bool = True
    enable_speech: bool = True
    enable_emotions: bool = True

class PersonaEngineIntegration:
    """DuckBot integration for Handcrafted Persona Engine"""

    def __init__(self, config: Optional[PersonaEngineConfig] = None):
        self.config = config or PersonaEngineConfig()
        self.available = PERSONA_ENGINE_AVAILABLE
        self.session = None
        
        if self.available:
            self._initialize_session()
        else:
            logger.warning("Handcrafted Persona Engine not available")

    def _initialize_session(self):
        """Initialize HTTP session for Persona Engine"""
        try:
            self.session = requests.Session()
            if self.config.api_key:
                self.session.headers.update({
                    "Authorization": f"Bearer {self.config.api_key}",
                    "X-API-Key": self.config.api_key
                })
            logger.info("Persona Engine integration session initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Persona Engine session: {e}")
            self.available = False

    async def start_persona_engine(self) -> Dict[str, Any]:
        """Start Persona Engine server"""
        if not self.available:
            return {"success": False, "error": "Persona Engine not available"}
            
        try:
            # Check if already running
            if await self._is_persona_engine_running():
                return {"success": True, "message": "Persona Engine already running", "url": self.config.base_url}
            
            # Start Persona Engine process
            # Assuming the engine can be started with a Python module
            cmd = [
                "python",
                "-m",
                "persona_engine",
                "--host", self.config.host,
                "--port", str(self.config.port),
                "--character", self.config.character_model,
                "--voice", self.config.voice_model
            ]
            
            if self.config.enable_animation:
                cmd.append("--enable-animation")
                
            if self.config.enable_speech:
                cmd.append("--enable-speech")
                
            if self.config.enable_emotions:
                cmd.append("--enable-emotions")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=Path(__file__).parent / "handcrafted-persona-engine"
            )
            
            # Wait for startup
            await asyncio.sleep(5)
            
            if await self._is_persona_engine_running():
                return {
                    "success": True,
                    "message": "Persona Engine started successfully",
                    "url": self.config.base_url,
                    "pid": process.pid
                }
            else:
                return {
                    "success": False,
                    "error": "Persona Engine failed to start",
                    "details": "Process may have exited"
                }
                
        except Exception as e:
            logger.error(f"Failed to start Persona Engine: {e}")
            return {"success": False, "error": str(e)}

    async def stop_persona_engine(self) -> Dict[str, Any]:
        """Stop Persona Engine server"""
        if not self.available:
            return {"success": False, "error": "Persona Engine not available"}
            
        try:
            # Check if running
            if not await self._is_persona_engine_running():
                return {"success": True, "message": "Persona Engine not running"}
            
            # Try graceful shutdown via API
            try:
                response = self.session.post(
                    f"{self.config.base_url}/api/shutdown",
                    timeout=self.config.timeout
                )
                if response.status_code == 200:
                    return {"success": True, "message": "Persona Engine shut down successfully"}
            except:
                pass
            
            # If API shutdown fails, try killing process
            try:
                # This would require finding the process by port
                import psutil
                for proc in psutil.process_iter(['pid', 'name', 'connections']):
                    try:
                        for conn in proc.connections():
                            if conn.laddr.port == self.config.port:
                                proc.terminate()
                                proc.wait(timeout=10)
                                return {"success": True, "message": "Persona Engine process terminated"}
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                        continue
            except ImportError:
                pass
                
            return {"success": False, "error": "Failed to stop Persona Engine"}
            
        except Exception as e:
            logger.error(f"Failed to stop Persona Engine: {e}")
            return {"success": False, "error": str(e)}

    async def _is_persona_engine_running(self) -> bool:
        """Check if Persona Engine is running"""
        try:
            response = self.session.get(
                f"{self.config.base_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False

    async def get_persona_engine_status(self) -> Dict[str, Any]:
        """Get Persona Engine status"""
        if not self.available:
            return {"success": False, "error": "Persona Engine not available"}
            
        try:
            running = await self._is_persona_engine_running()
            
            status = {
                "success": True,
                "running": running,
                "url": self.config.base_url,
                "host": self.config.host,
                "port": self.config.port,
                "character_model": self.config.character_model,
                "voice_model": self.config.voice_model,
                "features": {
                    "animation": self.config.enable_animation,
                    "speech": self.config.enable_speech,
                    "emotions": self.config.enable_emotions
                }
            }
            
            if running:
                try:
                    response = self.session.get(
                        f"{self.config.base_url}/api/status",
                        timeout=self.config.timeout
                    )
                    if response.status_code == 200:
                        status.update(response.json())
                except:
                    pass
                    
            return status
            
        except Exception as e:
            logger.error(f"Failed to get Persona Engine status: {e}")
            return {"success": False, "error": str(e)}

    async def generate_character_response(self, text: str, emotion: Optional[str] = None, 
                                       gesture: Optional[str] = None) -> Dict[str, Any]:
        """Generate character response with animation and voice"""
        if not self.available:
            return {"success": False, "error": "Persona Engine not available"}
            
        try:
            if not await self._is_persona_engine_running():
                start_result = await self.start_persona_engine()
                if not start_result["success"]:
                    return start_result
                    
            # Generate character response
            payload = {
                "text": text,
                "character": self.config.character_model,
                "voice": self.config.voice_model
            }
            
            if emotion:
                payload["emotion"] = emotion
                
            if gesture:
                payload["gesture"] = gesture
            
            response = self.session.post(
                f"{self.config.base_url}/api/generate",
                json=payload,
                timeout=self.config.timeout
            )
            
            if response.status_code == 200:
                return {"success": True, "result": response.json()}
            else:
                return {
                    "success": False,
                    "error": f"Persona Engine API error: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            logger.error(f"Failed to generate character response: {e}")
            return {"success": False, "error": str(e)}

    async def animate_character(self, animation: str, duration: Optional[float] = None) -> Dict[str, Any]:
        """Animate character with specific animation"""
        if not self.available:
            return {"success": False, "error": "Persona Engine not available"}
            
        try:
            if not await self._is_persona_engine_running():
                start_result = await self.start_persona_engine()
                if not start_result["success"]:
                    return start_result
                    
            # Animate character
            payload = {
                "animation": animation,
                "character": self.config.character_model
            }
            
            if duration:
                payload["duration"] = duration
            
            response = self.session.post(
                f"{self.config.base_url}/api/animate",
                json=payload,
                timeout=self.config.timeout
            )
            
            if response.status_code == 200:
                return {"success": True, "result": response.json()}
            else:
                return {
                    "success": False,
                    "error": f"Persona Engine API error: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            logger.error(f"Failed to animate character: {e}")
            return {"success": False, "error": str(e)}

    async def synthesize_speech(self, text: str, voice: Optional[str] = None, 
                              speed: Optional[float] = None) -> Dict[str, Any]:
        """Synthesize speech for character"""
        if not self.available:
            return {"success": False, "error": "Persona Engine not available"}
            
        try:
            if not await self._is_persona_engine_running():
                start_result = await self.start_persona_engine()
                if not start_result["success"]:
                    return start_result
                    
            # Synthesize speech
            payload = {
                "text": text,
                "voice": voice or self.config.voice_model,
                "character": self.config.character_model
            }
            
            if speed:
                payload["speed"] = speed
            
            response = self.session.post(
                f"{self.config.base_url}/api/speak",
                json=payload,
                timeout=self.config.timeout
            )
            
            if response.status_code == 200:
                return {"success": True, "result": response.json()}
            else:
                return {
                    "success": False,
                    "error": f"Persona Engine API error: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            logger.error(f"Failed to synthesize speech: {e}")
            return {"success": False, "error": str(e)}

    async def express_emotion(self, emotion: str, intensity: Optional[float] = None) -> Dict[str, Any]:
        """Express emotion on character"""
        if not self.available:
            return {"success": False, "error": "Persona Engine not available"}
            
        try:
            if not await self._is_persona_engine_running():
                start_result = await self.start_persona_engine()
                if not start_result["success"]:
                    return start_result
                    
            # Express emotion
            payload = {
                "emotion": emotion,
                "character": self.config.character_model
            }
            
            if intensity:
                payload["intensity"] = intensity
            
            response = self.session.post(
                f"{self.config.base_url}/api/emote",
                json=payload,
                timeout=self.config.timeout
            )
            
            if response.status_code == 200:
                return {"success": True, "result": response.json()}
            else:
                return {
                    "success": False,
                    "error": f"Persona Engine API error: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            logger.error(f"Failed to express emotion: {e}")
            return {"success": False, "error": str(e)}

    def get_status(self) -> Dict[str, Any]:
        """Get integration status"""
        return {
            "available": self.available,
            "configured": self.config is not None,
            "persona_engine_running": asyncio.run(self._is_persona_engine_running()) if self.available else False,
            "host": self.config.host if self.config else None,
            "port": self.config.port if self.config else None,
            "base_url": self.config.base_url if self.config else None,
            "character_model": self.config.character_model if self.config else None,
            "voice_model": self.config.voice_model if self.config else None,
            "features": {
                "animation": self.config.enable_animation if self.config else False,
                "speech": self.config.enable_speech if self.config else False,
                "emotions": self.config.enable_emotions if self.config else False
            } if self.config else {}
        }

# Global instance
persona_engine_integration = PersonaEngineIntegration()

async def initialize_persona_engine() -> bool:
    """Initialize Persona Engine integration"""
    global persona_engine_integration
    persona_engine_integration = PersonaEngineIntegration()
    return persona_engine_integration.available

async def start_persona_engine() -> Dict[str, Any]:
    """Start Persona Engine"""
    return await persona_engine_integration.start_persona_engine()

async def stop_persona_engine() -> Dict[str, Any]:
    """Stop Persona Engine"""
    return await persona_engine_integration.stop_persona_engine()

async def get_persona_engine_status() -> Dict[str, Any]:
    """Get Persona Engine status"""
    return await persona_engine_integration.get_persona_engine_status()

async def generate_character_response(text: str, emotion: Optional[str] = None, 
                                   gesture: Optional[str] = None) -> Dict[str, Any]:
    """Generate character response with animation and voice"""
    return await persona_engine_integration.generate_character_response(text, emotion, gesture)

async def animate_character(animation: str, duration: Optional[float] = None) -> Dict[str, Any]:
    """Animate character with specific animation"""
    return await persona_engine_integration.animate_character(animation, duration)

async def synthesize_speech(text: str, voice: Optional[str] = None, 
                          speed: Optional[float] = None) -> Dict[str, Any]:
    """Synthesize speech for character"""
    return await persona_engine_integration.synthesize_speech(text, voice, speed)

async def express_emotion(emotion: str, intensity: Optional[float] = None) -> Dict[str, Any]:
    """Express emotion on character"""
    return await persona_engine_integration.express_emotion(emotion, intensity)

def get_persona_engine_integration_status() -> Dict[str, Any]:
    """Get Persona Engine integration status"""
    return persona_engine_integration.get_status()

def is_persona_engine_available() -> bool:
    """Check if Persona Engine is available"""
    return persona_engine_integration.available