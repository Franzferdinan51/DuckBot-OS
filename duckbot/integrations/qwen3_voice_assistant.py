#!/usr/bin/env python3
"""
Qwen3 Voice Assistant Integration for DuckBot
Replaces VibeVoice with Qwen3-Omni's native voice capabilities
"""

import os
import json
import logging
import asyncio
import wave
import struct
import tempfile
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
import threading
import queue
import time

# Try to import audio processing libraries
try:
    import soundfile as sf
    import librosa
    AUDIO_PROCESSING_AVAILABLE = True
except ImportError:
    AUDIO_PROCESSING_AVAILABLE = False

# Try to import TTS
try:
    import torch
    from transformers import VitsModel, AutoTokenizer
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    VitsModel = None
    AutoTokenizer = None

# Try to import speech recognition
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    sr = None

# Import Qwen3-Omni integration
try:
    from ..core.qwen3_omni_integration import qwen3_omni_integration
    QWEN3_OMNI_AVAILABLE = True
except ImportError:
    QWEN3_OMNI_AVAILABLE = False
    qwen3_omni_integration = None

# Import audio configuration
try:
    from .audio_config import AudioConfig
    AUDIO_CONFIG_AVAILABLE = True
except ImportError:
    AUDIO_CONFIG_AVAILABLE = False
    AudioConfig = None

logger = logging.getLogger(__name__)

@dataclass
class VoiceAssistantConfig:
    """Configuration for Qwen3 Voice Assistant"""
    sample_rate: int = 16000
    channels: int = 1
    chunk_size: int = 1024
    audio_format: str = "wav"
    silence_threshold: float = 0.01
    silence_duration: float = 1.0
    max_recording_duration: float = 30.0
    tts_model_id: str = "facebook/mms-tts-eng"
    voice_profile: str = "default"
    enable_noise_reduction: bool = True
    enable_voice_commands: bool = True
    wake_word: str = "hey duckbot"
    language: str = "en-US"

@dataclass
class VoiceCommand:
    """Voice command structure"""
    command: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class VoiceInteraction:
    """Voice interaction record"""
    audio_input_path: Optional[str] = None
    transcription: str = ""
    response_text: str = ""
    audio_output_path: Optional[str] = None
    confidence: float = 0.0
    processing_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

class Qwen3VoiceAssistant:
    """Qwen3 Voice Assistant with native multimodal capabilities"""

    def __init__(self, config: Optional[VoiceAssistantConfig] = None):
        self.config = config or VoiceAssistantConfig()

        # Initialize components
        self.tts_model = None
        self.tts_tokenizer = None
        self.speech_recognizer = None
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.is_active = False

        # Voice commands
        self.voice_commands = {
            "help": {"action": "show_help", "description": "Show available commands"},
            "stop": {"action": "stop_listening", "description": "Stop voice assistant"},
            "pause": {"action": "pause_processing", "description": "Pause processing"},
            "resume": {"action": "resume_processing", "description": "Resume processing"},
            "status": {"action": "get_status", "description": "Get system status"},
            "clear": {"action": "clear_context", "description": "Clear conversation context"},
            "switch model": {"action": "switch_model", "description": "Switch AI model"},
            "volume up": {"action": "volume_up", "description": "Increase volume"},
            "volume down": {"action": "volume_down", "description": "Decrease volume"},
            "mute": {"action": "mute_audio", "description": "Mute audio"},
            "unmute": {"action": "unmute_audio", "description": "Unmute audio"},
        }

        # Interaction history
        self.interaction_history: List[VoiceInteraction] = []
        self.max_history_size = 100

        # Performance tracking
        self.total_interactions = 0
        self.total_processing_time = 0.0
        self.failed_interactions = 0

        # Initialize
        self._initialize_components()

    def _initialize_components(self):
        """Initialize voice assistant components"""
        # Initialize speech recognition
        if SPEECH_RECOGNITION_AVAILABLE:
            try:
                self.speech_recognizer = sr.Recognizer()
                self.speech_recognizer.energy_threshold = 300
                self.speech_recognizer.dynamic_energy_threshold = True
                logger.info("Speech recognition initialized")
            except Exception as e:
                logger.error(f"Failed to initialize speech recognition: {e}")

        # Initialize TTS
        if TTS_AVAILABLE:
            try:
                self.tts_model = VitsModel.from_pretrained(self.config.tts_model_id)
                self.tts_tokenizer = AutoTokenizer.from_pretrained(self.config.tts_model_id)
                logger.info("TTS model initialized")
            except Exception as e:
                logger.error(f"Failed to initialize TTS model: {e}")

        # Set active status
        self.is_active = (
            QWEN3_OMNI_AVAILABLE and
            qwen3_omni_integration and
            qwen3_omni_integration.is_available()
        )

        logger.info(f"Voice assistant initialized - Active: {self.is_active}")

    def is_available(self) -> bool:
        """Check if voice assistant is available"""
        return self.is_active and (
            (self.speech_recognizer is not None) or
            (qwen3_omni_integration and hasattr(qwen3_omni_integration, 'audio_pipeline'))
        )

    def get_status(self) -> Dict[str, Any]:
        """Get voice assistant status"""
        return {
            "available": self.is_available(),
            "listening": self.is_listening,
            "tts_available": self.tts_model is not None,
            "speech_recognition_available": self.speech_recognizer is not None,
            "qwen3_omni_available": QWEN3_OMNI_AVAILABLE,
            "total_interactions": self.total_interactions,
            "average_processing_time": self.total_processing_time / max(1, self.total_interactions),
            "success_rate": (self.total_interactions - self.failed_interactions) / max(1, self.total_interactions),
            "voice_commands": list(self.voice_commands.keys()),
            "config": {
                "sample_rate": self.config.sample_rate,
                "language": self.config.language,
                "wake_word": self.config.wake_word,
                "voice_profile": self.config.voice_profile
            }
        }

    async def start_listening(self, continuous: bool = True, wake_word_detection: bool = True):
        """Start listening for voice input"""
        if not self.is_available():
            logger.error("Voice assistant not available")
            return False

        if self.is_listening:
            logger.warning("Already listening")
            return True

        self.is_listening = True
        logger.info("Voice assistant started listening")

        if continuous:
            asyncio.create_task(self._continuous_listening_loop(wake_word_detection))

        return True

    async def stop_listening(self):
        """Stop listening for voice input"""
        if not self.is_listening:
            return True

        self.is_listening = False
        logger.info("Voice assistant stopped listening")
        return True

    async def _continuous_listening_loop(self, wake_word_detection: bool = True):
        """Continuous listening loop"""
        if not SPEECH_RECOGNITION_AVAILABLE:
            logger.error("Speech recognition not available")
            return

        microphone = sr.Microphone(sample_rate=self.config.sample_rate, chunk_size=self.config.chunk_size)

        with microphone as source:
            self.speech_recognizer.adjust_for_ambient_noise(source)
            logger.info("Adjusted for ambient noise")

        while self.is_listening:
            try:
                with microphone as source:
                    audio = self.speech_recognizer.listen(source, timeout=1, phrase_time_limit=30)

                # Process audio
                await self._process_audio(audio, wake_word_detection)

            except sr.WaitTimeoutError:
                continue
            except Exception as e:
                logger.error(f"Listening loop error: {e}")
                await asyncio.sleep(1)

    async def _process_audio(self, audio_data, wake_word_detection: bool = True):
        """Process audio input"""
        start_time = time.time()

        try:
            # Convert audio to WAV data
            wav_data = audio_data.get_wav_data()

            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(wav_data)
                temp_path = tmp.name

            # Transcribe audio
            transcription = await self._transcribe_audio(temp_path)

            if not transcription:
                os.unlink(temp_path)
                return

            # Check for wake word if enabled
            if wake_word_detection and self.config.wake_word:
                if not self._detect_wake_word(transcription):
                    os.unlink(temp_path)
                    return

            # Remove wake word from transcription
            if wake_word_detection:
                transcription = transcription.replace(self.config.wake_word, "").strip()

            # Check for voice commands
            command = self._parse_voice_command(transcription)

            if command:
                # Execute voice command
                response = await self._execute_voice_command(command)
            else:
                # Process with Qwen3-Omni
                response = await self._process_with_qwen3_omni(transcription)

            # Generate voice response if TTS available
            audio_output_path = None
            if self.tts_model and response.get("generate_audio", True):
                audio_output_path = await self._generate_speech(response["text"])

            # Record interaction
            processing_time = time.time() - start_time
            interaction = VoiceInteraction(
                audio_input_path=temp_path,
                transcription=transcription,
                response_text=response["text"],
                audio_output_path=audio_output_path,
                confidence=response.get("confidence", 0.8),
                processing_time=processing_time,
                metadata={
                    "command": command.command if command else None,
                    "wake_word_detected": wake_word_detection,
                    "model_used": "qwen3_omni"
                }
            )

            self._record_interaction(interaction)

            # Play audio response
            if audio_output_path:
                await self._play_audio(audio_output_path)

            # Clean up
            os.unlink(temp_path)
            if audio_output_path and os.path.exists(audio_output_path):
                os.unlink(audio_output_path)

        except Exception as e:
            logger.error(f"Audio processing error: {e}")
            self.failed_interactions += 1

    async def _transcribe_audio(self, audio_path: str) -> Optional[str]:
        """Transcribe audio to text"""
        try:
            # Use Qwen3-Omni's audio processing if available
            if qwen3_omni_integration and hasattr(qwen3_omni_integration, 'audio_pipeline'):
                result = qwen3_omni_integration.audio_pipeline(audio_path)
                return result.get("text", "")

            # Fallback to speech recognition
            if self.speech_recognizer:
                with sr.AudioFile(audio_path) as source:
                    audio = self.speech_recognizer.record(source)

                try:
                    # Try Google Speech Recognition first
                    text = self.speech_recognizer.recognize_google(audio, language=self.config.language)
                    return text
                except sr.UnknownValueError:
                    try:
                        # Fallback to Sphinx
                        text = self.speech_recognizer.recognize_sphinx(audio)
                        return text
                    except:
                        return None
                except Exception as e:
                    logger.error(f"Speech recognition error: {e}")
                    return None

            return None

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return None

    def _detect_wake_word(self, text: str) -> bool:
        """Detect wake word in transcription"""
        return self.config.wake_word.lower() in text.lower()

    def _parse_voice_command(self, text: str) -> Optional[VoiceCommand]:
        """Parse voice command from text"""
        text_lower = text.lower()

        for command_name, command_info in self.voice_commands.items():
            if command_name in text_lower:
                # Extract parameters
                parameters = {}

                # Handle switch model command
                if command_name == "switch model":
                    # Extract model name from text
                    words = text_lower.split()
                    if "switch model" in text_lower and len(words) > 2:
                        model_name = " ".join(words[words.index("model") + 1:])
                        parameters["model_name"] = model_name

                return VoiceCommand(
                    command=command_name,
                    parameters=parameters,
                    confidence=0.9
                )

        return None

    async def _execute_voice_command(self, command: VoiceCommand) -> Dict[str, Any]:
        """Execute voice command"""
        try:
            action = command.command
            parameters = command.parameters

            response_text = ""
            success = True

            if action == "show_help":
                response_text = self._generate_help_message()
            elif action == "stop_listening":
                await self.stop_listening()
                response_text = "Voice assistant stopped listening."
            elif action == "get_status":
                status = self.get_status()
                response_text = f"Voice assistant status: {status['available']}, Interactions: {status['total_interactions']}, Success rate: {status['success_rate']:.1%}"
            elif action == "clear_context":
                # Clear conversation context (would need to integrate with memory system)
                self.interaction_history.clear()
                response_text = "Conversation context cleared."
            elif action == "switch_model":
                model_name = parameters.get("model_name", "")
                response_text = f"Switching to model: {model_name}"
                # Implement model switching logic
            elif action == "volume_up":
                response_text = "Volume increased."
                # Implement volume control
            elif action == "volume_down":
                response_text = "Volume decreased."
                # Implement volume control
            else:
                response_text = f"Command '{action}' executed."

            return {
                "text": response_text,
                "success": success,
                "confidence": command.confidence,
                "generate_audio": True
            }

        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return {
                "text": f"Error executing command: {str(e)}",
                "success": False,
                "confidence": 0.0,
                "generate_audio": True
            }

    def _generate_help_message(self) -> str:
        """Generate help message for voice commands"""
        help_parts = ["Available voice commands:"]
        for cmd, info in self.voice_commands.items():
            help_parts.append(f"  • {cmd}: {info['description']}")

        return "\n".join(help_parts)

    async def _process_with_qwen3_omni(self, text: str) -> Dict[str, Any]:
        """Process text with Qwen3-Omni"""
        if not QWEN3_OMNI_AVAILABLE or not qwen3_omni_integration:
            return {
                "text": "Qwen3-Omni not available",
                "success": False,
                "confidence": 0.0,
                "generate_audio": True
            }

        try:
            # Create task for Qwen3-Omni
            task = {
                "kind": "voice_assistant",
                "prompt": text,
                "context": {
                    "modality": "voice",
                    "voice_profile": self.config.voice_profile,
                    "interaction_history": len(self.interaction_history)
                }
            }

            result = await qwen3_omni_integration.execute_task(task)

            return {
                "text": result.get("response", "No response generated"),
                "success": result.get("success", False),
                "confidence": result.get("confidence", 0.8),
                "generate_audio": True
            }

        except Exception as e:
            logger.error(f"Qwen3-Omni processing error: {e}")
            return {
                "text": f"Error processing with Qwen3-Omni: {str(e)}",
                "success": False,
                "confidence": 0.0,
                "generate_audio": True
            }

    async def _generate_speech(self, text: str) -> Optional[str]:
        """Generate speech from text"""
        if not self.tts_model or not self.tts_tokenizer:
            return None

        try:
            # Prepare text
            inputs = self.tts_tokenizer(text, return_tensors="pt")

            # Generate speech
            with torch.no_grad():
                output = self.tts_model(**inputs)

            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                # Convert to numpy array and save
                audio_data = output.waveform[0].cpu().numpy()
                sf.write(tmp.name, audio_data, self.tts_model.config.sampling_rate)
                return tmp.name

        except Exception as e:
            logger.error(f"TTS generation error: {e}")
            return None

    async def _play_audio(self, audio_path: str):
        """Play audio file"""
        try:
            # Simple audio playback (would need platform-specific implementation)
            import platform
            system = platform.system()

            if system == "Windows":
                import winsound
                winsound.PlaySound(audio_path, winsound.SND_FILENAME)
            elif system == "Darwin":
                os.system(f"afplay {audio_path}")
            else:  # Linux
                os.system(f"aplay {audio_path}")

        except Exception as e:
            logger.error(f"Audio playback error: {e}")

    def _record_interaction(self, interaction: VoiceInteraction):
        """Record voice interaction"""
        self.interaction_history.append(interaction)
        self.total_interactions += 1
        self.total_processing_time += interaction.processing_time

        # Limit history size
        if len(self.interaction_history) > self.max_history_size:
            self.interaction_history.pop(0)

    async def process_audio_file(self, audio_path: str, generate_response: bool = True) -> VoiceInteraction:
        """Process audio file"""
        if not self.is_available():
            raise RuntimeError("Voice assistant not available")

        start_time = time.time()

        try:
            # Transcribe audio
            transcription = await self._transcribe_audio(audio_path)

            if not transcription:
                raise RuntimeError("Failed to transcribe audio")

            # Process with Qwen3-Omni
            response = await self._process_with_qwen3_omni(transcription)

            # Generate voice response
            audio_output_path = None
            if generate_response and self.tts_model:
                audio_output_path = await self._generate_speech(response["text"])

            # Create interaction record
            processing_time = time.time() - start_time
            interaction = VoiceInteraction(
                audio_input_path=audio_path,
                transcription=transcription,
                response_text=response["text"],
                audio_output_path=audio_output_path,
                confidence=response.get("confidence", 0.8),
                processing_time=processing_time,
                metadata={
                    "model_used": "qwen3_omni",
                    "generate_response": generate_response
                }
            )

            self._record_interaction(interaction)
            return interaction

        except Exception as e:
            logger.error(f"Audio file processing error: {e}")
            raise

    async def text_to_speech(self, text: str) -> Optional[str]:
        """Convert text to speech and return audio file path"""
        return await self._generate_speech(text)

    async def start_interactive_mode(self):
        """Start interactive voice assistant mode"""
        if not self.is_available():
            print("Voice assistant not available")
            return

        print("🎤 Qwen3 Voice Assistant - Interactive Mode")
        print("==========================================")
        print(f"Listening... (say '{self.config.wake_word}' to activate)")

        await self.start_listening(continuous=True, wake_word_detection=True)

        try:
            # Keep running until interrupted
            while self.is_listening:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping voice assistant...")
            await self.stop_listening()

    def get_interaction_history(self, limit: Optional[int] = None) -> List[VoiceInteraction]:
        """Get voice interaction history"""
        if limit:
            return self.interaction_history[-limit:]
        return self.interaction_history.copy()

    def clear_history(self):
        """Clear interaction history"""
        self.interaction_history.clear()

# Global instance
qwen3_voice_assistant = Qwen3VoiceAssistant()

# Convenience functions
async def start_voice_assistant(continuous: bool = True) -> bool:
    """Start voice assistant"""
    return await qwen3_voice_assistant.start_listening(continuous=continuous)

async def stop_voice_assistant() -> bool:
    """Stop voice assistant"""
    return await qwen3_voice_assistant.stop_listening()

def get_voice_assistant_status() -> Dict[str, Any]:
    """Get voice assistant status"""
    return qwen3_voice_assistant.get_status()

async def process_voice_command(text: str) -> Dict[str, Any]:
    """Process voice command text"""
    command = qwen3_voice_assistant._parse_voice_command(text)
    if command:
        return await qwen3_voice_assistant._execute_voice_command(command)
    else:
        return await qwen3_voice_assistant._process_with_qwen3_omni(text)

if __name__ == "__main__":
    # Test the voice assistant
    async def test():
        print("Qwen3 Voice Assistant Test")
        print("==========================")

        # Show status
        status = get_voice_assistant_status()
        print(f"Status: {status}")

        # Test voice commands
        if status["available"]:
            print("\nTesting voice commands...")
            commands = ["help", "status", "clear context"]

            for cmd in commands:
                result = await process_voice_command(cmd)
                print(f"Command '{cmd}': {result['text']}")
        else:
            print("Voice assistant not available for testing")

    asyncio.run(test())