#!/usr/bin/env python3
"""
Qwen3-Omni Integration Module for DuckBot
Main brain implementation with Flash Attention 2 support and multimodal capabilities
"""

import os
import json
import logging
import asyncio
import torch
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
import traceback
from PIL import Image
import soundfile as sf
import tempfile
import warnings

# Suppress specific warnings
warnings.filterwarnings("ignore", category=UserWarning, module="transformers")

# Try to import transformers
try:
    from transformers import (
        AutoTokenizer,
        AutoModelForCausalLM,
        AutoModelForVision2Seq,
        AutoProcessor,
        Qwen2AudioForConditionalGeneration,
        Qwen2AudioProcessor,
        Qwen2_5OmniForConditionalGeneration,
        Qwen2_5OmniProcessor,
        Qwen3OmniMoeForConditionalGeneration,
        Qwen3OmniMoeProcessor,
        Qwen2TokenizerFast,
        pipeline
    )
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    AutoTokenizer = None
    AutoModelForCausalLM = None
    AutoModelForVision2Seq = None
    AutoProcessor = None
    Qwen2AudioForConditionalGeneration = None
    Qwen2AudioProcessor = None
    Qwen2_5OmniForConditionalGeneration = None
    Qwen2_5OmniProcessor = None
    Qwen3OmniMoeForConditionalGeneration = None
    Qwen3OmniMoeProcessor = None
    Qwen2TokenizerFast = None
    pipeline = None

# Try to import flash attention
try:
    import flash_attn
    FLASH_ATTENTION_AVAILABLE = True
except ImportError:
    FLASH_ATTENTION_AVAILABLE = False

# Try to import audio processing
try:
    import librosa
    AUDIO_PROCESSING_AVAILABLE = True
except ImportError:
    AUDIO_PROCESSING_AVAILABLE = False

# Import configuration manager
try:
    from .ai_configuration_manager import AIConfigurationManager
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    AIConfigurationManager = None

# Import memory integration
try:
    from ..integrations.memento_integration import memento_system
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    memento_system = None

logger = logging.getLogger(__name__)

@dataclass
class Qwen3OmniConfig:
    """Configuration for Qwen3-Omni integration"""
    model_id: str = "./models/Qwen3-Omni-30B-A3B-Instruct"
    device: str = "auto"
    dtype: str = "auto"
    use_flash_attention: bool = True
    max_memory: Dict[str, str] = field(default_factory=lambda: {"gpu": "24GB", "cpu": "32GB"})
    max_length: int = 32768
    temperature: float = 0.7
    top_p: float = 0.9
    repetition_penalty: float = 1.1
    do_sample: bool = True
    cache_dir: Optional[str] = None
    trust_remote_code: bool = True
    use_fast_tokenizer: bool = True
    load_in_8bit: bool = False
    load_in_4bit: bool = False
    device_map: str = "auto"

@dataclass
class MultimodalInput:
    """Multimodal input container"""
    text: Optional[str] = None
    image: Optional[Union[str, Image.Image, np.ndarray]] = None
    audio: Optional[Union[str, np.ndarray]] = None
    video: Optional[Union[str, np.ndarray]] = None
    context: Optional[Dict[str, Any]] = None

@dataclass
class Qwen3OmniResponse:
    """Response from Qwen3-Omni"""
    text: str
    confidence: float
    usage: Dict[str, Any]
    processing_time: float
    multimodal_features: List[str] = field(default_factory=list)
    audio_response: Optional[str] = None
    reasoning: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class Qwen3OmniIntegration:
    """Qwen3-Omni integration with Flash Attention 2 support"""

    def __init__(self, config: Optional[Qwen3OmniConfig] = None):
        self.config = config or Qwen3OmniConfig()

        # Initialize components
        self.model = None
        self.tokenizer = None
        self.processor = None
        self.device = None
        self.is_loaded = False
        self.load_time = None

        # Performance tracking
        self.call_count = 0
        self.total_tokens = 0
        self.total_processing_time = 0.0
        self.error_count = 0

        # Audio processing
        self.audio_pipeline = None
        self.voice_assistant = None

        # Memory integration
        self.memory_system = memento_system if MEMORY_AVAILABLE else None

        # Initialize
        self._initialize_device()

    def _initialize_device(self):
        """Initialize device configuration"""
        if self.config.device == "auto":
            if torch.cuda.is_available():
                self.device = "cuda"
                # Check for flash attention support
                if FLASH_ATTENTION_AVAILABLE and self.config.use_flash_attention:
                    try:
                        # Check if device supports flash attention
                        device_capability = torch.cuda.get_device_capability()
                        if device_capability >= (8, 0):  # Ampere or newer
                            logger.info("Flash Attention 2: Enabled (device supported)")
                        else:
                            logger.warning("Flash Attention 2: Device not supported, using standard attention")
                            self.config.use_flash_attention = False
                    except Exception as e:
                        logger.warning(f"Flash Attention 2 detection failed: {e}")
                        self.config.use_flash_attention = False
            else:
                self.device = "cpu"
                self.config.use_flash_attention = False
        else:
            self.device = self.config.device

        logger.info(f"Device: {self.device}")
        logger.info(f"Flash Attention 2: {'Enabled' if self.config.use_flash_attention else 'Disabled'}")

    async def load_model(self):
        """Load Qwen3-Omni model with Flash Attention 2 support"""
        if self.is_loaded:
            return True

        try:
            start_time = datetime.now()
            logger.info(f"Loading Qwen3-Omni model: {self.config.model_id}")

            if not TRANSFORMERS_AVAILABLE:
                raise ImportError("Transformers library not available. Please install transformers>=4.40.0")

            # Prepare load arguments
            load_kwargs = {
                "trust_remote_code": self.config.trust_remote_code,
                "cache_dir": self.config.cache_dir,
            }

            # Configure device map and memory
            if self.device == "cuda":
                if self.config.load_in_4bit:
                    load_kwargs["load_in_4bit"] = True
                    load_kwargs["device_map"] = self.config.device_map
                elif self.config.load_in_8bit:
                    load_kwargs["load_in_8bit"] = True
                    load_kwargs["device_map"] = self.config.device_map
                else:
                    load_kwargs["torch_dtype"] = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
                    load_kwargs["device_map"] = self.config.device_map

                    # Configure flash attention
                    if self.config.use_flash_attention and FLASH_ATTENTION_AVAILABLE:
                        load_kwargs["attn_implementation"] = "flash_attention_2"
                        logger.info("Using Flash Attention 2 for improved performance")
            else:
                load_kwargs["device_map"] = "cpu"
                load_kwargs["torch_dtype"] = torch.float32

            # Load model using correct Qwen3OmniMoe architecture
            self.model = Qwen3OmniMoeForConditionalGeneration.from_pretrained(
                self.config.model_id,
                **load_kwargs
            )
            logger.info("Qwen3OmniMoeForConditionalGeneration loaded successfully")

            # Load processor for multimodal inputs (Qwen3-Omni specific)
            try:
                self.processor = Qwen3OmniMoeProcessor.from_pretrained(
                    self.config.model_id,
                    trust_remote_code=self.config.trust_remote_code,
                    cache_dir=self.config.cache_dir,
                )
                logger.info("Qwen3OmniMoeProcessor loaded successfully")

                # Get tokenizer from processor
                self.tokenizer = self.processor.tokenizer
                logger.info("Qwen3-Omni processor and tokenizer loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load Qwen3-Omni processor: {e}")
                raise

            # Initialize audio pipeline if available
            if AUDIO_PROCESSING_AVAILABLE:
                self.audio_pipeline = pipeline(
                    "automatic-speech-recognition",
                    model="openai/whisper-large-v3",
                    device=0 if self.device == "cuda" else -1
                )
                logger.info("Audio processing pipeline initialized")

            self.is_loaded = True
            self.load_time = (datetime.now() - start_time).total_seconds()

            logger.info(f"Qwen3-Omni loaded successfully in {self.load_time:.2f}s")
            return True

        except Exception as e:
            self.error_count += 1
            logger.error(f"Failed to load Qwen3-Omni: {str(e)}")
            logger.error(traceback.format_exc())
            return False

    def is_available(self) -> bool:
        """Check if Qwen3-Omni is available and ready"""
        return self.is_loaded and self.model is not None and self.tokenizer is not None

    def get_status(self) -> Dict[str, Any]:
        """Get current status of Qwen3-Omni integration"""
        return {
            "available": self.is_available(),
            "model_id": self.config.model_id,
            "device": self.device,
            "flash_attention": self.config.use_flash_attention,
            "load_time": self.load_time,
            "call_count": self.call_count,
            "total_tokens": self.total_tokens,
            "total_processing_time": self.total_processing_time,
            "average_tokens_per_call": self.total_tokens / max(1, self.call_count),
            "average_processing_time": self.total_processing_time / max(1, self.call_count),
            "error_rate": self.error_count / max(1, self.call_count),
            "memory_available": self._get_memory_info(),
            "capabilities": [
                "text_generation",
                "multimodal_processing",
                "voice_assistant",
                "reasoning",
                "coding",
                "analysis"
            ] if self.is_available() else []
        }

    def _get_memory_info(self) -> Dict[str, Any]:
        """Get memory information"""
        try:
            if self.device == "cuda":
                memory_info = torch.cuda.get_device_properties(0)
                return {
                    "gpu_memory_total": f"{memory_info.total_memory / 1024**3:.1f}GB",
                    "gpu_memory_used": f"{torch.cuda.memory_allocated() / 1024**3:.1f}GB",
                    "gpu_memory_cached": f"{torch.cuda.memory_reserved() / 1024**3:.1f}GB"
                }
            else:
                import psutil
                memory = psutil.virtual_memory()
                return {
                    "cpu_memory_total": f"{memory.total / 1024**3:.1f}GB",
                    "cpu_memory_used": f"{memory.used / 1024**3:.1f}GB",
                    "cpu_memory_percent": f"{memory.percent:.1f}%"
                }
        except Exception as e:
            logger.warning(f"Failed to get memory info: {e}")
            return {}

    async def process_multimodal_input(self, input_data: MultimodalInput) -> Qwen3OmniResponse:
        """Process multimodal input with Qwen3-Omni"""
        if not self.is_available():
            await self.load_model()

        if not self.is_available():
            raise RuntimeError("Qwen3-Omni is not available")

        start_time = datetime.now()
        self.call_count += 1

        try:
            # Prepare input based on modalities
            multimodal_features = []
            prompt_parts = []

            # Text input
            if input_data.text:
                prompt_parts.append(input_data.text)

            # Image processing
            image_tensor = None
            if input_data.image is not None:
                if isinstance(input_data.image, str):
                    # Load image from file
                    try:
                        image = Image.open(input_data.image)
                        image_tensor = self.processor.image_processor(image, return_tensors="pt").pixel_values
                        multimodal_features.append("vision")
                    except Exception as e:
                        logger.warning(f"Failed to load image: {e}")
                elif isinstance(input_data.image, Image.Image):
                    image_tensor = self.processor.image_processor(input_data.image, return_tensors="pt").pixel_values
                    multimodal_features.append("vision")
                elif isinstance(input_data.image, np.ndarray):
                    image = Image.fromarray(input_data.image)
                    image_tensor = self.processor.image_processor(image, return_tensors="pt").pixel_values
                    multimodal_features.append("vision")

            # Audio processing
            audio_text = None
            if input_data.audio is not None and self.audio_pipeline:
                try:
                    if isinstance(input_data.audio, str):
                        # Load audio from file
                        audio_text = self.audio_pipeline(input_data.audio)["text"]
                    elif isinstance(input_data.audio, np.ndarray):
                        # Process numpy array
                        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                            sf.write(tmp.name, input_data.audio, 16000)
                            audio_text = self.audio_pipeline(tmp.name)["text"]
                            os.unlink(tmp.name)

                    if audio_text:
                        prompt_parts.append(f"[Audio: {audio_text}]")
                        multimodal_features.append("audio")
                except Exception as e:
                    logger.warning(f"Failed to process audio: {e}")

            # Combine text parts
            full_prompt = " ".join(prompt_parts) if prompt_parts else "Process the provided multimodal input."

            # Prepare generation arguments
            generation_kwargs = {
                "max_new_tokens": self.config.max_length,
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "repetition_penalty": self.config.repetition_penalty,
                "do_sample": self.config.do_sample,
                "pad_token_id": self.tokenizer.eos_token_id,
            }

            # Prepare inputs for model - Qwen3OmniMoe has specific requirements
            inputs = self.tokenizer(full_prompt, return_tensors="pt", truncation=True, max_length=self.config.max_length)

            # Move to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # For Qwen3OmniMoe, we may need to handle multimodal inputs differently
            if image_tensor is not None:
                # For now, just use text input for Qwen3OmniMoe
                # TODO: Implement proper multimodal input handling for Qwen3OmniMoe
                pass

            # Generate response
            with torch.no_grad():
                try:
                    if self.config.use_flash_attention and FLASH_ATTENTION_AVAILABLE:
                        # Use flash attention for generation
                        with torch.backends.cuda.sdp_kernel(enable_flash=True):
                            outputs = self.model.generate(**inputs, **generation_kwargs)
                    else:
                        outputs = self.model.generate(**inputs, **generation_kwargs)
                except Exception as e:
                    # Fallback to simpler generation parameters
                    logger.warning(f"Generation with complex parameters failed: {e}")
                    simple_kwargs = {
                        "max_new_tokens": min(512, self.config.max_length),
                        "temperature": 0.7,
                        "do_sample": True,
                        "pad_token_id": self.tokenizer.eos_token_id,
                    }
                    outputs = self.model.generate(**inputs, **simple_kwargs)

            # Decode response
            response_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Remove original prompt if present
            if full_prompt in response_text:
                response_text = response_text.replace(full_prompt, "").strip()

            # Calculate usage statistics
            input_tokens = inputs["input_ids"].shape[1]
            output_tokens = len(outputs[0]) - input_tokens
            self.total_tokens += input_tokens + output_tokens

            processing_time = (datetime.now() - start_time).total_seconds()
            self.total_processing_time += processing_time

            # Store in memory if available
            if self.memory_system and input_data.text:
                try:
                    await self.memory_system.store_conversation(
                        role="user",
                        content=input_data.text,
                        metadata={
                            "modalities": multimodal_features,
                            "response_length": len(response_text),
                            "processing_time": processing_time
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to store conversation in memory: {e}")

            return Qwen3OmniResponse(
                text=response_text,
                confidence=min(1.0, output_tokens / 100),  # Simple confidence estimation
                usage={
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens
                },
                processing_time=processing_time,
                multimodal_features=multimodal_features,
                metadata={
                    "model": self.config.model_id,
                    "device": self.device,
                    "flash_attention": self.config.use_flash_attention
                }
            )

        except Exception as e:
            self.error_count += 1
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Multimodal processing failed: {str(e)}")
            logger.error(traceback.format_exc())

            return Qwen3OmniResponse(
                text=f"Error processing multimodal input: {str(e)}",
                confidence=0.0,
                usage={"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
                processing_time=processing_time,
                multimodal_features=[],
                metadata={"error": str(e)}
            )

    async def generate_text(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> Qwen3OmniResponse:
        """Generate text response from prompt"""
        multimodal_input = MultimodalInput(text=prompt, context=context)
        return await self.process_multimodal_input(multimodal_input)

    async def process_image(self, image_path: str, prompt: str = "Describe this image in detail.") -> Qwen3OmniResponse:
        """Process image with text prompt"""
        multimodal_input = MultimodalInput(text=prompt, image=image_path)
        return await self.process_multimodal_input(multimodal_input)

    async def process_audio(self, audio_path: str, prompt: str = "Transcribe and analyze this audio.") -> Qwen3OmniResponse:
        """Process audio with text prompt"""
        multimodal_input = MultimodalInput(text=prompt, audio=audio_path)
        return await self.process_multimodal_input(multimodal_input)

    async def voice_interaction(self, audio_input: Union[str, np.ndarray], response_mode: str = "text") -> Dict[str, Any]:
        """Handle voice interaction with optional voice response"""
        try:
            # Process audio input
            audio_result = await self.process_audio(audio_input, "Transcribe the audio and provide a helpful response.")

            if response_mode == "voice":
                # Generate voice response (would require TTS integration)
                # For now, return text with voice flag
                return {
                    "success": True,
                    "transcription": audio_result.text,
                    "response": audio_result.text,
                    "response_mode": "text",  # Placeholder for actual voice
                    "confidence": audio_result.confidence,
                    "processing_time": audio_result.processing_time
                }
            else:
                return {
                    "success": True,
                    "transcription": audio_result.text,
                    "response": audio_result.text,
                    "response_mode": "text",
                    "confidence": audio_result.confidence,
                    "processing_time": audio_result.processing_time
                }

        except Exception as e:
            logger.error(f"Voice interaction failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "response_mode": response_mode
            }

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task using Qwen3-Omni"""
        task_type = task.get("kind", "general")
        prompt = task.get("prompt", "")
        context = task.get("context", {})

        try:
            # Prepare multimodal input
            multimodal_features = []

            # Handle different task types
            if task_type == "code":
                # Add code-specific context
                prompt = f"Code Task: {prompt}\n\nPlease provide a complete, well-commented solution."
                multimodal_features.append("coding")
            elif task_type == "analysis":
                prompt = f"Analysis Task: {prompt}\n\nPlease provide detailed analysis and insights."
                multimodal_features.append("analysis")
            elif task_type == "reasoning":
                prompt = f"Reasoning Task: {prompt}\n\nPlease provide step-by-step logical reasoning."
                multimodal_features.append("reasoning")

            # Check for multimodal elements in context
            if "image_path" in context:
                response = await self.process_image(context["image_path"], prompt)
            elif "audio_path" in context:
                response = await self.process_audio(context["audio_path"], prompt)
            else:
                response = await self.generate_text(prompt, context)

            return {
                "success": True,
                "response": response.text,
                "confidence": response.confidence,
                "usage": response.usage,
                "processing_time": response.processing_time,
                "multimodal_features": response.multimodal_features,
                "task_type": task_type,
                "metadata": response.metadata
            }

        except Exception as e:
            self.error_count += 1
            logger.error(f"Task execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "task_type": task_type
            }

    async def unload_model(self):
        """Unload model to free memory"""
        if self.is_loaded:
            try:
                del self.model
                del self.tokenizer
                if self.processor:
                    del self.processor
                if self.audio_pipeline:
                    del self.audio_pipeline

                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    torch.cuda.ipc_collect()

                self.model = None
                self.tokenizer = None
                self.processor = None
                self.audio_pipeline = None
                self.is_loaded = False

                logger.info("Qwen3-Omni model unloaded successfully")

            except Exception as e:
                logger.error(f"Failed to unload model: {e}")

    def __del__(self):
        """Cleanup on destruction"""
        if hasattr(self, 'is_loaded') and self.is_loaded:
            try:
                asyncio.get_event_loop().run_until_complete(self.unload_model())
            except:
                pass

# Global instance
qwen3_omni_integration = Qwen3OmniIntegration()

# Convenience functions
async def process_with_qwen3_omni(input_data: Union[str, MultimodalInput, Dict[str, Any]]) -> Qwen3OmniResponse:
    """Process input with Qwen3-Omni"""
    if isinstance(input_data, str):
        return await qwen3_omni_integration.generate_text(input_data)
    elif isinstance(input_data, MultimodalInput):
        return await qwen3_omni_integration.process_multimodal_input(input_data)
    elif isinstance(input_data, dict):
        return Qwen3OmniResponse(
            text=(await qwen3_omni_integration.execute_task(input_data)).get("response", ""),
            confidence=0.8,
            usage={},
            processing_time=0.0,
            multimodal_features=[]
        )
    else:
        raise ValueError("Unsupported input type")

def get_qwen3_omni_status() -> Dict[str, Any]:
    """Get Qwen3-Omni status"""
    return qwen3_omni_integration.get_status()

async def execute_qwen3_task(task: Dict[str, Any]) -> Dict[str, Any]:
    """Execute task with Qwen3-Omni"""
    return await qwen3_omni_integration.execute_task(task)

if __name__ == "__main__":
    # Test the integration
    async def test():
        print("Qwen3-Omni Integration Test")
        print("============================")

        # Show status
        status = get_qwen3_omni_status()
        print(f"Status: {status}")

        # Test text generation
        if status["available"]:
            print("\nTesting text generation...")
            result = await process_with_qwen3_omni("Hello! I am Qwen3-Omni, your AI assistant. How can I help you today?")
            print(f"Response: {result.text}")
            print(f"Processing time: {result.processing_time:.2f}s")
            print(f"Usage: {result.usage}")
        else:
            print("Model not available for testing")

    asyncio.run(test())