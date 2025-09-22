"""
Real Microsoft VibeVoice Integration
Uses the real Microsoft VibeVoice server with proper multi-speaker capabilities
"""
import asyncio
import aiohttp
import json
import os
import tempfile
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import logging
import yaml

from ..core.cost_management import CostTracker

logger = logging.getLogger(__name__)

class RealVibeVoiceClient:
    """Client for real Microsoft VibeVoice TTS API."""

    def __init__(self,
                 api_url: str = "http://localhost:8000",
                 config_path: Optional[str] = None,
                 cost_tracker: Optional[CostTracker] = None):
        """
        Initialize Real VibeVoice client.

        Args:
            api_url: VibeVoice FastAPI server URL
            config_path: Path to configuration file
            cost_tracker: Optional cost tracking instance
        """
        self.api_url = api_url.rstrip('/')
        self.cost_tracker = cost_tracker
        self.session = None
        self.config = self._load_config(config_path)

        # Voice configurations from config
        self.voice_presets = self.config.get("vibevoice", {}).get("voice_profiles", {
            "en-alice": {"name": "Alice", "gender": "female", "pitch": 0.0, "speed": 1.0},
            "en-carter": {"name": "Carter", "gender": "male", "pitch": -2.0, "speed": 1.0},
            "en-david": {"name": "David", "gender": "male", "pitch": 1.0, "speed": 0.9},
            "en-emily": {"name": "Emily", "gender": "female", "pitch": 1.5, "speed": 1.1},
            "zh-xiaoli": {"name": "Xiaoli", "gender": "female", "pitch": 0.0, "speed": 1.0},
            "zh-wang": {"name": "Wang", "gender": "male", "pitch": -1.0, "speed": 1.0}
        })

        # Available voices
        self.available_voices = self.config.get("vibevoice", {}).get("available_voices",
            ["en-alice", "en-carter", "en-david", "en-emily", "zh-xiaoli", "zh-wang"])

        # Default settings
        self.default_config = {
            "cfg_scale": 1.3,
            "temperature": 0.7,
            "max_length": 2048,
            "style": "conversational",
            "emotion": "neutral"
        }

        self.enabled = self.config.get("vibevoice", {}).get("enabled", True)
        self.initialized = False

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file."""
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                logger.error(f"Error loading config from {config_path}: {e}")

        # Try default config path
        default_config_path = Path(__file__).parent.parent.parent / "config" / "ai_providers_config.yaml"
        if default_config_path.exists():
            try:
                with open(default_config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                logger.error(f"Error loading default config: {e}")

        # Return default configuration
        return {
            "vibevoice": {
                "enabled": True,
                "api_url": "http://localhost:8000",
                "default_voice": "en-alice"
            }
        }

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def initialize(self) -> bool:
        """Initialize the VibeVoice client and test connection."""
        if not self.enabled:
            logger.info("VibeVoice disabled in configuration")
            self.initialized = False
            return False

        try:
            if not self.session:
                self.session = aiohttp.ClientSession()

            # Test connection to server
            connected = await self.test_connection()
            if connected:
                # Get available voices
                voices_info = await self.get_available_voices()
                logger.info(f"VibeVoice connected with {len(voices_info.get('voices', []))} voices")
                self.initialized = True
                return True
            else:
                logger.warning("VibeVoice server not available")
                self.initialized = False
                return False

        except Exception as e:
            logger.error(f"Failed to initialize VibeVoice: {e}")
            self.initialized = False
            return False

    async def test_connection(self) -> bool:
        """Test connection to VibeVoice API server."""
        try:
            if not self.session:
                return False

            async with self.session.get(f"{self.api_url}/health", timeout=10) as response:
                if response.status == 200:
                    health_data = await response.json()
                    return health_data.get("status") == "healthy"
                return False
        except Exception as e:
            logger.error(f"VibeVoice connection test failed: {e}")
            return False

    async def get_available_voices(self) -> Dict[str, Any]:
        """Get list of available voice presets."""
        try:
            if not self.session:
                return {"voices": self.available_voices}

            async with self.session.get(f"{self.api_url}/voices", timeout=10) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.warning(f"Failed to get voices from API: {response.status}")
                    return {"voices": self.available_voices}
        except Exception as e:
            logger.error(f"Error getting voices: {e}")
            return {"voices": self.available_voices}

    async def generate_speech(self,
                            text: str,
                            speakers: Optional[List[str]] = None,
                            voice_style: str = "conversational",
                            emotion: str = "neutral",
                            output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate speech using real Microsoft VibeVoice TTS.

        Args:
            text: Text to convert to speech (can include speaker labels)
            speakers: List of speaker voices to use
            voice_style: Style of speech generation
            emotion: Emotion for speech generation
            output_dir: Directory to save audio file

        Returns:
            Dict with generation status and file path
        """
        try:
            if not self.initialized:
                if not await self.initialize():
                    return {"success": False, "error": "VibeVoice not initialized"}

            # Prepare script format
            formatted_script = await self._format_script(text, speakers)

            # Prepare speaker names
            speaker_names = speakers or ["en-alice"]
            valid_speakers = [s for s in speaker_names if s in self.available_voices]

            if not valid_speakers:
                valid_speakers = ["en-alice"]

            # Create generation request
            request_data = {
                "script": formatted_script,
                "speaker_names": valid_speakers,
                "cfg_scale": self.default_config["cfg_scale"],
                "style": voice_style,
                "emotion": emotion
            }

            logger.info(f"VibeVoice generation request: {len(text)} chars, {len(valid_speakers)} speakers, style: {voice_style}, emotion: {emotion}")

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
                # Track usage
                if self.cost_tracker:
                    await self._track_usage(text, len(valid_speakers), voice_style, emotion)

                return {
                    "success": True,
                    "task_id": task_id,
                    "audio_path": audio_path,
                    "speakers": valid_speakers,
                    "voice_style": voice_style,
                    "emotion": emotion,
                    "text_length": len(text),
                    "model_used": "Microsoft VibeVoice"
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
        """Format text into VibeVoice script format."""
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
        """Wait for generation to complete and download result."""
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
                            await asyncio.sleep(2)
                            continue

                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"Error checking status for task {task_id}: {e}")
                await asyncio.sleep(2)

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

    async def _track_usage(self, text: str, speaker_count: int, style: str, emotion: str):
        """Track VibeVoice usage for analytics."""
        if not self.cost_tracker:
            return

        try:
            usage_data = {
                "provider": "vibevoice",
                "model": "microsoft_vibevoice",
                "text_length": len(text),
                "speaker_count": speaker_count,
                "style": style,
                "emotion": emotion,
                "timestamp": datetime.now().isoformat(),
                "cost": 0.0  # Free service
            }

            await self.cost_tracker.track_custom_usage("tts", usage_data)

        except Exception as e:
            logger.error(f"Error tracking VibeVoice usage: {e}")

    # Enhanced methods for advanced features

    async def generate_emotional_speech(self,
                                      text: str,
                                      emotion: str = "neutral",
                                      speaker: str = "en-alice",
                                      intensity: float = 0.5,
                                      output_dir: Optional[str] = None) -> Optional[str]:
        """Generate speech with specific emotion."""
        try:
            result = await self.generate_speech(
                text=text,
                speakers=[speaker],
                voice_style="emotional",
                emotion=emotion,
                output_dir=output_dir
            )

            return result.get("audio_path") if result.get("success") else None

        except Exception as e:
            logger.error(f"Error generating emotional speech: {e}")
            return None

    async def generate_conversation(self,
                                  script: List[Dict[str, str]],
                                  style: str = "conversational",
                                  output_dir: Optional[str] = None) -> Optional[str]:
        """Generate multi-turn conversation."""
        try:
            # Format script for VibeVoice
            formatted_script = "\n".join([f"{turn['speaker']}: {turn['text']}" for turn in script])

            # Extract unique speakers
            speakers = list(set(turn['speaker'] for turn in script))

            result = await self.generate_speech(
                text=formatted_script,
                speakers=speakers,
                voice_style=style,
                emotion="neutral",
                output_dir=output_dir
            )

            return result.get("audio_path") if result.get("success") else None

        except Exception as e:
            logger.error(f"Error generating conversation: {e}")
            return None

    async def generate_podcast_segment(self,
                                     content: Dict[str, Any],
                                     output_dir: Optional[str] = None) -> Dict[str, Any]:
        """Generate a podcast segment with multiple speakers."""
        try:
            script = []

            # Add intro
            if content.get("intro"):
                script.append({
                    "speaker": content.get("host_voice", "en-alice"),
                    "text": content["intro"]
                })

            # Add main content
            for segment in content.get("segments", []):
                if segment.get("type") == "monologue":
                    script.append({
                        "speaker": segment.get("voice", "en-alice"),
                        "text": segment["text"]
                    })
                elif segment.get("type") == "dialogue":
                    for turn in segment.get("conversation", []):
                        script.append({
                            "speaker": turn.get("speaker", "en-alice"),
                            "text": turn.get("text", "")
                        })

            # Add outro
            if content.get("outro"):
                script.append({
                    "speaker": content.get("host_voice", "en-alice"),
                    "text": content["outro"]
                })

            # Generate audio
            audio_path = await self.generate_conversation(
                script=script,
                style="professional",
                output_dir=output_dir
            )

            return {
                "success": audio_path is not None,
                "audio_path": audio_path,
                "segment_count": len(script),
                "content": content
            }

        except Exception as e:
            logger.error(f"Error generating podcast segment: {e}")
            return {"success": False, "error": str(e)}

    async def batch_generate(self,
                           items: List[Dict[str, Any]],
                           output_dir: Optional[str] = None) -> List[Dict[str, Any]]:
        """Generate multiple audio files in batch."""
        try:
            results = []

            # Process items concurrently
            tasks = []
            for item in items:
                task = self._generate_single_item(item, output_dir)
                tasks.append(task)

            # Wait for all generations to complete
            generation_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for i, result in enumerate(generation_results):
                if isinstance(result, Exception):
                    results.append({
                        "success": False,
                        "error": str(result),
                        "item": items[i]
                    })
                else:
                    results.append({
                        "success": True,
                        "result": result,
                        "item": items[i]
                    })

            return results

        except Exception as e:
            logger.error(f"Error in batch generation: {e}")
            return []

    async def _generate_single_item(self, item: Dict[str, Any], output_dir: Optional[str]) -> Dict[str, Any]:
        """Generate a single audio item."""
        try:
            item_type = item.get("type", "single")

            if item_type == "single":
                audio_path = await self.generate_speech(
                    text=item["text"],
                    speakers=item.get("speakers", ["en-alice"]),
                    voice_style=item.get("style", "conversational"),
                    emotion=item.get("emotion", "neutral"),
                    output_dir=output_dir
                )
            elif item_type == "emotional":
                audio_path = await self.generate_emotional_speech(
                    text=item["text"],
                    emotion=item.get("emotion", "neutral"),
                    speaker=item.get("speaker", "en-alice"),
                    intensity=item.get("intensity", 0.5),
                    output_dir=output_dir
                )
            elif item_type == "conversation":
                audio_path = await self.generate_conversation(
                    script=item["script"],
                    style=item.get("style", "conversational"),
                    output_dir=output_dir
                )
            else:
                return {"success": False, "error": f"Unknown item type: {item_type}"}

            if audio_path:
                return {"success": True, "audio_path": audio_path}
            else:
                return {"success": False, "error": "Generation failed"}

        except Exception as e:
            logger.error(f"Error generating single item: {e}")
            return {"success": False, "error": str(e)}

    async def get_service_health(self) -> Dict[str, Any]:
        """Get comprehensive health status of VibeVoice service."""
        try:
            health_info = {
                "service_available": self.enabled,
                "client_initialized": self.initialized,
                "api_url": self.api_url,
                "timestamp": datetime.now().isoformat(),
                "config": self.config.get("vibevoice", {})
            }

            if self.enabled and self.initialized:
                # Test connection
                connection_test = await self.test_connection()
                health_info["connection_status"] = connection_test

                if connection_test:
                    # Get available voices
                    voices_info = await self.get_available_voices()
                    health_info["available_voices"] = len(voices_info.get("voices", []))
                    health_info["voice_list"] = voices_info.get("voices", [])

                # Get server health
                try:
                    async with self.session.get(f"{self.api_url}/health", timeout=10) as response:
                        if response.status == 200:
                            server_health = await response.json()
                            health_info["server_health"] = server_health
                except:
                    pass

            return health_info

        except Exception as e:
            logger.error(f"Error getting VibeVoice health: {e}")
            return {"service_available": False, "error": str(e)}

    def get_capabilities(self) -> Dict[str, Any]:
        """Get VibeVoice capabilities."""
        return {
            "available": self.enabled and self.initialized,
            "service_type": "tts",
            "multi_speaker": True,
            "emotional_support": True,
            "style_transfer": True,
            "batch_processing": True,
            "podcast_generation": True,
            "max_duration": "90 minutes",
            "supported_languages": ["en", "zh"],
            "voice_count": len(self.available_voices),
            "features": [
                "Multi-speaker TTS",
                "Emotional speech synthesis",
                "Style transfer",
                "Batch processing",
                "Podcast generation",
                "Real-time voice chat",
                "Next-token diffusion",
                "7.5Hz tokenizers"
            ] if self.enabled and self.initialized else ["Basic TTS only"]
        }

# Global instance
class RealDuckBotVibeVoice:
    """DuckBot VibeVoice integration using real Microsoft VibeVoice."""

    def __init__(self, config_path: Optional[str] = None, cost_tracker: Optional[CostTracker] = None):
        self.client = RealVibeVoiceClient(config_path=config_path, cost_tracker=cost_tracker)
        self.available = False
        self.capabilities = {}
        self._initialization_lock = asyncio.Lock()

    async def initialize(self) -> bool:
        """Initialize VibeVoice client."""
        async with self._initialization_lock:
            try:
                initialized = await self.client.initialize()
                self.available = initialized

                if initialized:
                    self.capabilities = self.client.get_capabilities()
                    logger.info("[OK] Real Microsoft VibeVoice integration initialized")
                else:
                    logger.warning("[WARN] Real Microsoft VibeVoice not available")

                return initialized

            except Exception as e:
                logger.error(f"Failed to initialize real VibeVoice: {e}")
                self.available = False
                return False

    async def generate_speech(self, text: str, speakers: Optional[List[str]] = None, **kwargs) -> Dict[str, Any]:
        """Generate speech using real Microsoft VibeVoice."""
        if not await self.initialize():
            return {"success": False, "error": "VibeVoice not available"}

        try:
            return await self.client.generate_speech(
                text=text,
                speakers=speakers,
                voice_style=kwargs.get("style", "conversational"),
                emotion=kwargs.get("emotion", "neutral"),
                output_dir=kwargs.get("output_dir")
            )
        except Exception as e:
            logger.error(f"Real VibeVoice generation error: {e}")
            return {"success": False, "error": str(e)}

    def get_capabilities(self) -> Dict[str, Any]:
        """Get VibeVoice capabilities."""
        return self.capabilities or self.client.get_capabilities()

    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        try:
            if not self.available:
                await self.initialize()

            health = await self.client.get_service_health()
            health["integration_available"] = self.available
            return health
        except Exception as e:
            logger.error(f"Error getting real VibeVoice health: {e}")
            return {"available": False, "error": str(e)}

# Global instance
real_vibevoice_integration = RealDuckBotVibeVoice()

async def initialize_real_vibevoice() -> bool:
    """Initialize the real VibeVoice integration."""
    return await real_vibevoice_integration.initialize()

def is_real_vibevoice_available() -> bool:
    """Check if real VibeVoice is available."""
    return real_vibevoice_integration.available

def get_real_vibevoice_capabilities() -> Dict[str, Any]:
    """Get real VibeVoice capabilities."""
    return real_vibevoice_integration.get_capabilities()

async def generate_real_vibevoice_speech(text: str, speakers: Optional[List[str]] = None, **kwargs) -> Dict[str, Any]:
    """Generate speech using real Microsoft VibeVoice."""
    return await real_vibevoice_integration.generate_speech(text, speakers, **kwargs)

async def get_real_vibevoice_health() -> Dict[str, Any]:
    """Get real VibeVoice health status."""
    return await real_vibevoice_integration.get_health_status()