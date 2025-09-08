"""
VibeVoice TTS Integration for DuckBot
Microsoft's open-source multi-speaker text-to-speech system
"""
import asyncio
import aiohttp
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import logging

from .cost_tracker import CostTracker

logger = logging.getLogger(__name__)

class VibeVoiceClient:
    """Client for VibeVoice TTS API integration."""
    
    def __init__(self, 
                 api_url: str = "http://localhost:8000",
                 cost_tracker: Optional[CostTracker] = None):
        """
        Initialize VibeVoice client.
        
        Args:
            api_url: VibeVoice FastAPI server URL
            cost_tracker: Optional cost tracking instance
        """
        self.api_url = api_url.rstrip('/')
        self.cost_tracker = cost_tracker
        self.session = None
        
        # Voice configurations
        self.voice_presets = {
            # English voices
            "en-alice": "en-Alice_woman",
            "en-carter": "en-Carter_man", 
            "en-david": "en-David_man",
            "en-emily": "en-Emily_woman",
            
            # Chinese voices (if needed)
            "zh-xiaoli": "zh-XiaoLi_woman",
            "zh-wang": "zh-Wang_man"
        }
        
        # Default settings
        self.default_config = {
            "cfg_scale": 1.3,
            "temperature": 0.7,
            "max_length": 2048
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def get_available_voices(self) -> Dict[str, Any]:
        """Get list of available voice presets."""
        try:
            async with self.session.get(f"{self.api_url}/voices") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to get voices: {response.status}")
                    return {"voices": list(self.voice_presets.values())}
        except Exception as e:
            logger.error(f"Error getting voices: {e}")
            return {"voices": list(self.voice_presets.values())}
    
    async def generate_speech(self,
                            text: str,
                            speakers: Optional[List[str]] = None,
                            voice_style: str = "conversational",
                            output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate speech using VibeVoice TTS.
        
        Args:
            text: Text to convert to speech (can include speaker labels)
            speakers: List of speaker voices to use
            voice_style: Style of speech generation
            output_dir: Directory to save audio file
            
        Returns:
            Dict with generation status and file path
        """
        try:
            # Prepare script format
            formatted_script = await self._format_script(text, speakers)
            
            # Prepare speaker names
            speaker_names = speakers or ["en-alice", "en-carter"]
            voice_names = [self.voice_presets.get(s, s) for s in speaker_names]
            
            # Create generation request
            request_data = {
                "script": formatted_script,
                "speaker_names": voice_names,
                "cfg_scale": self.default_config["cfg_scale"]
            }
            
            logger.info(f"VibeVoice generation request: {len(text)} chars, {len(voice_names)} speakers")
            
            # Submit generation request
            async with self.session.post(
                f"{self.api_url}/generate",
                json=request_data,
                timeout=30
            ) as response:
                
                if response.status != 200:
                    error_msg = f"VibeVoice API error: {response.status}"
                    logger.error(error_msg)
                    return {"success": False, "error": error_msg}
                
                result = await response.json()
                task_id = result.get("task_id")
                
                if not task_id:
                    return {"success": False, "error": "No task ID returned"}
            
            # Poll for completion
            audio_path = await self._wait_for_completion(task_id, output_dir)
            
            if audio_path:
                # Track costs (VibeVoice is free but track usage)
                if self.cost_tracker:
                    await self._track_usage(text, len(voice_names))
                
                return {
                    "success": True,
                    "task_id": task_id,
                    "audio_path": audio_path,
                    "speakers": voice_names,
                    "text_length": len(text)
                }
            else:
                return {"success": False, "error": "Generation failed or timed out"}
                
        except asyncio.TimeoutError:
            logger.error("VibeVoice request timed out")
            return {"success": False, "error": "Request timed out"}
        except Exception as e:
            logger.error(f"VibeVoice generation error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _format_script(self, text: str, speakers: Optional[List[str]]) -> str:
        """
        Format text into VibeVoice script format.
        
        Args:
            text: Input text
            speakers: Speaker names
            
        Returns:
            Formatted script with speaker labels
        """
        if not speakers:
            speakers = ["Speaker1", "Speaker2"]
        
        # If text already has speaker labels, return as-is
        if any(speaker in text for speaker in speakers):
            return text
        
        # If text contains dialogue markers, parse them
        if ":" in text and "\n" in text:
            lines = text.strip().split('\n')
            formatted_lines = []
            
            for line in lines:
                line = line.strip()
                if ":" in line:
                    # Already has speaker format
                    formatted_lines.append(line)
                elif line:
                    # Assign to first speaker by default
                    formatted_lines.append(f"{speakers[0]}: {line}")
            
            return '\n'.join(formatted_lines)
        
        # Simple single speaker text
        return f"{speakers[0]}: {text}"
    
    async def _wait_for_completion(self, 
                                 task_id: str, 
                                 output_dir: Optional[str],
                                 max_wait: int = 300) -> Optional[str]:
        """
        Wait for generation to complete and download result.
        
        Args:
            task_id: Generation task ID
            output_dir: Directory to save audio
            max_wait: Maximum wait time in seconds
            
        Returns:
            Path to generated audio file or None if failed
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                # Check status
                async with self.session.get(f"{self.api_url}/status/{task_id}") as response:
                    if response.status == 200:
                        status_data = await response.json()
                        status = status_data.get("status")
                        
                        if status == "completed":
                            # Download result
                            return await self._download_result(task_id, output_dir)
                        elif status == "failed":
                            logger.error(f"VibeVoice generation failed for task {task_id}")
                            return None
                        elif status in ["pending", "processing"]:
                            # Still processing, wait
                            await asyncio.sleep(5)
                            continue
                
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error checking status for task {task_id}: {e}")
                await asyncio.sleep(5)
        
        logger.error(f"VibeVoice generation timed out for task {task_id}")
        return None
    
    async def _download_result(self, task_id: str, output_dir: Optional[str]) -> Optional[str]:
        """Download the generated audio file."""
        try:
            async with self.session.get(f"{self.api_url}/result/{task_id}") as response:
                if response.status == 200:
                    # Determine output path
                    if output_dir:
                        os.makedirs(output_dir, exist_ok=True)
                        output_path = Path(output_dir) / f"vibevoice_{task_id}.wav"
                    else:
                        # Use temp directory
                        temp_dir = Path(tempfile.gettempdir()) / "duckbot_voice"
                        temp_dir.mkdir(exist_ok=True)
                        output_path = temp_dir / f"vibevoice_{task_id}.wav"
                    
                    # Save audio file
                    audio_data = await response.read()
                    with open(output_path, 'wb') as f:
                        f.write(audio_data)
                    
                    logger.info(f"VibeVoice audio saved: {output_path}")
                    return str(output_path)
                else:
                    logger.error(f"Failed to download result for task {task_id}: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error downloading result for task {task_id}: {e}")
            return None
    
    async def _track_usage(self, text: str, speaker_count: int):
        """Track VibeVoice usage for analytics (free service)."""
        if not self.cost_tracker:
            return
        
        try:
            # VibeVoice is free but track usage metrics
            usage_data = {
                "provider": "vibevoice",
                "model": "vibevoice-1.5b",
                "text_length": len(text),
                "speaker_count": speaker_count,
                "timestamp": datetime.now().isoformat(),
                "cost": 0.0  # Free service
            }
            
            await self.cost_tracker.track_custom_usage("tts", usage_data)
            
        except Exception as e:
            logger.error(f"Error tracking VibeVoice usage: {e}")
    
    async def test_connection(self) -> bool:
        """Test connection to VibeVoice API server."""
        try:
            async with self.session.get(f"{self.api_url}/voices", timeout=10) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"VibeVoice connection test failed: {e}")
            return False

class VibeVoiceManager:
    """High-level manager for VibeVoice integration."""
    
    def __init__(self, cost_tracker: Optional[CostTracker] = None):
        self.cost_tracker = cost_tracker
        self.client = None
        self.api_url = os.getenv("VIBEVOICE_API_URL", "http://localhost:8000")
        self.enabled = os.getenv("ENABLE_VIBEVOICE", "true").lower() == "true"
    
    async def initialize(self) -> bool:
        """Initialize VibeVoice client and test connection."""
        if not self.enabled:
            logger.info("VibeVoice disabled in configuration")
            return False
        
        try:
            self.client = VibeVoiceClient(self.api_url, self.cost_tracker)
            
            async with self.client:
                connected = await self.client.test_connection()
                if connected:
                    logger.info("VibeVoice connection established")
                    return True
                else:
                    logger.warning("VibeVoice server not available")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to initialize VibeVoice: {e}")
            return False
    
    async def generate_voice_content(self,
                                   content: str,
                                   speakers: Optional[List[str]] = None,
                                   style: str = "conversational") -> Optional[str]:
        """
        Generate voice content using VibeVoice.
        
        Args:
            content: Text content to convert
            speakers: Voice speakers to use
            style: Voice generation style
            
        Returns:
            Path to generated audio file or None if failed
        """
        if not self.enabled or not self.client:
            logger.warning("VibeVoice not available")
            return None
        
        try:
            async with self.client:
                result = await self.client.generate_speech(
                    text=content,
                    speakers=speakers,
                    voice_style=style
                )
                
                if result.get("success"):
                    return result.get("audio_path")
                else:
                    logger.error(f"VibeVoice generation failed: {result.get('error')}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error generating voice content: {e}")
            return None
    
    def get_available_voices(self) -> List[str]:
        """Get list of available voice options."""
        return [
            "en-alice", "en-carter", "en-david", "en-emily",
            "zh-xiaoli", "zh-wang"
        ]
    
    def is_available(self) -> bool:
        """Check if VibeVoice is available and enabled."""
        return self.enabled and self.client is not None