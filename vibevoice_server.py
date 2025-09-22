"""
Mock VibeVoice TTS Server
Provides a compatible API for the VibeVoice client using alternative TTS systems
"""
import asyncio
import json
import logging
import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import time

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

# Import TTS alternatives
import edge_tts
import pyttsx3
from TTS.api import TTS as CoquiTTS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="VibeVoice TTS Server", version="1.0.0")

# Store for task statuses
task_storage = {}

# Available voices mapping
VOICE_MAP = {
    "en-alice": "en-US-AriaNeural",
    "en-carter": "en-US-GuyNeural",
    "en-david": "en-US-ChristopherNeural",
    "en-emily": "en-US-JennyNeural",
    "zh-xiaoli": "zh-CN-XiaoxiaoNeural",
    "zh-wang": "zh-CN-YunxiNeural"
}

class GenerateRequest(BaseModel):
    """Request model for speech generation"""
    script: str
    speaker_names: List[str]
    cfg_scale: float = 1.3

class GenerateResponse(BaseModel):
    """Response model for generation request"""
    task_id: str
    status: str
    message: str

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "VibeVoice TTS Server (Mock)",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/voices")
async def get_voices():
    """Get available voices"""
    voices = []
    for voice_id, voice_name in VOICE_MAP.items():
        voices.append({
            "id": voice_id,
            "name": voice_name,
            "language": voice_id.split("-")[0],
            "gender": "female" if "alice" in voice_id or "emily" in voice_id or "xiaoli" in voice_id else "male"
        })

    return {"voices": voices, "total": len(voices)}

@app.post("/generate", response_model=GenerateResponse)
async def generate_speech(request: GenerateRequest):
    """Generate speech using alternative TTS systems"""
    try:
        task_id = str(uuid.uuid4())

        # Store task info
        task_storage[task_id] = {
            "status": "processing",
            "created_at": datetime.now().isoformat(),
            "request": request.dict(),
            "progress": 0
        }

        logger.info(f"Started generation task {task_id}")

        # Start background processing
        asyncio.create_task(process_generation(task_id, request))

        return GenerateResponse(
            task_id=task_id,
            status="processing",
            message="Generation started"
        )

    except Exception as e:
        logger.error(f"Error starting generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_generation(task_id: str, request: GenerateRequest):
    """Process TTS generation in background"""
    try:
        # Update status
        task_storage[task_id]["status"] = "processing"
        task_storage[task_id]["progress"] = 10

        # Parse script and generate audio
        audio_segments = []

        # Split script by speaker
        lines = request.script.strip().split('\n')
        current_speaker = request.speaker_names[0] if request.speaker_names else "en-alice"

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # Check if line has speaker label
            if ':' in line:
                parts = line.split(':', 1)
                speaker_name = parts[0].strip()
                text = parts[1].strip()

                # Map speaker name to voice
                if speaker_name in request.speaker_names:
                    current_speaker = speaker_name
                elif speaker_name.lower() in ['speaker1', 'speaker 1']:
                    current_speaker = request.speaker_names[0] if request.speaker_names else "en-alice"
                elif speaker_name.lower() in ['speaker2', 'speaker 2']:
                    current_speaker = request.speaker_names[1] if len(request.speaker_names) > 1 else "en-alice"
            else:
                text = line

            # Generate audio for this segment
            task_storage[task_id]["progress"] = 20 + (i * 60 // len(lines))

            # Use Edge TTS for primary generation
            try:
                audio_path = await generate_with_edge_tts(text, current_speaker, task_id, i)
                if audio_path:
                    audio_segments.append(audio_path)
            except Exception as e:
                logger.warning(f"Edge TTS failed for segment {i}: {e}")
                # Fallback to pyttsx3
                try:
                    audio_path = await generate_with_pyttsx3(text, current_speaker, task_id, i)
                    if audio_path:
                        audio_segments.append(audio_path)
                except Exception as e2:
                    logger.error(f"Both TTS systems failed for segment {i}: {e2}")

        # Combine audio segments if multiple
        if len(audio_segments) > 1:
            combined_path = await combine_audio_segments(audio_segments, task_id)
            task_storage[task_id]["audio_path"] = combined_path
        elif audio_segments:
            task_storage[task_id]["audio_path"] = audio_segments[0]
        else:
            raise Exception("No audio segments generated")

        # Mark as completed
        task_storage[task_id]["status"] = "completed"
        task_storage[task_id]["progress"] = 100
        task_storage[task_id]["completed_at"] = datetime.now().isoformat()

        logger.info(f"Generation completed for task {task_id}")

    except Exception as e:
        logger.error(f"Generation failed for task {task_id}: {e}")
        task_storage[task_id]["status"] = "failed"
        task_storage[task_id]["error"] = str(e)
        task_storage[task_id]["failed_at"] = datetime.now().isoformat()

async def generate_with_edge_tts(text: str, speaker: str, task_id: str, segment_id: int) -> Optional[str]:
    """Generate audio using Edge TTS"""
    try:
        voice = VOICE_MAP.get(speaker, "en-US-AriaNeural")
        communicate = edge_tts.Communicate(text, voice=voice)

        # Create temp file
        temp_dir = Path(tempfile.gettempdir()) / "vibevoice" / task_id
        temp_dir.mkdir(parents=True, exist_ok=True)

        audio_path = temp_dir / f"segment_{segment_id}.mp3"

        await communicate.save(str(audio_path))

        logger.debug(f"Edge TTS generated: {audio_path}")
        return str(audio_path)

    except Exception as e:
        logger.error(f"Edge TTS generation failed: {e}")
        raise

async def generate_with_pyttsx3(text: str, speaker: str, task_id: str, segment_id: int) -> Optional[str]:
    """Generate audio using pyttsx3"""
    try:
        engine = pyttsx3.init()

        # Set voice properties based on speaker
        if "alice" in speaker or "emily" in speaker or "xiaoli" in speaker:
            engine.setProperty('rate', 180)  # Female voice rate
        else:
            engine.setProperty('rate', 160)  # Male voice rate

        # Create temp file
        temp_dir = Path(tempfile.gettempdir()) / "vibevoice" / task_id
        temp_dir.mkdir(parents=True, exist_ok=True)

        audio_path = temp_dir / f"segment_{segment_id}_fallback.wav"

        engine.save_to_file(text, str(audio_path))
        engine.runAndWait()

        logger.debug(f"pyttsx3 generated: {audio_path}")
        return str(audio_path)

    except Exception as e:
        logger.error(f"pyttsx3 generation failed: {e}")
        raise

async def combine_audio_segments(audio_paths: List[str], task_id: str) -> str:
    """Combine multiple audio segments into one file"""
    try:
        # For now, just return the first segment
        # In a full implementation, you'd use pydub or similar to combine audio
        return audio_paths[0]

    except Exception as e:
        logger.error(f"Audio combination failed: {e}")
        return audio_paths[0]  # Fallback to first segment

@app.get("/status/{task_id}")
async def get_status(task_id: str):
    """Get generation status"""
    if task_id not in task_storage:
        raise HTTPException(status_code=404, detail="Task not found")

    task = task_storage[task_id]

    return {
        "task_id": task_id,
        "status": task["status"],
        "progress": task.get("progress", 0),
        "created_at": task.get("created_at"),
        "completed_at": task.get("completed_at"),
        "error": task.get("error")
    }

@app.get("/result/{task_id}")
async def get_result(task_id: str):
    """Get generated audio file"""
    if task_id not in task_storage:
        raise HTTPException(status_code=404, detail="Task not found")

    task = task_storage[task_id]

    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="Task not completed")

    audio_path = task.get("audio_path")
    if not audio_path or not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found")

    return FileResponse(
        audio_path,
        media_type="audio/wav",
        filename=f"vibevoice_{task_id}.wav"
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "VibeVoice TTS Server (Mock)",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "available_voices": len(VOICE_MAP),
        "active_tasks": len([t for t in task_storage.values() if t["status"] == "processing"])
    }

@app.delete("/task/{task_id}")
async def delete_task(task_id: str):
    """Delete a task and its files"""
    if task_id not in task_storage:
        raise HTTPException(status_code=404, detail="Task not found")

    task = task_storage[task_id]

    # Clean up audio files
    audio_path = task.get("audio_path")
    if audio_path and os.path.exists(audio_path):
        try:
            os.remove(audio_path)
        except Exception as e:
            logger.warning(f"Failed to delete audio file: {e}")

    # Clean up temp directory
    temp_dir = Path(tempfile.gettempdir()) / "vibevoice" / task_id
    if temp_dir.exists():
        try:
            import shutil
            shutil.rmtree(temp_dir)
        except Exception as e:
            logger.warning(f"Failed to delete temp directory: {e}")

    # Remove from storage
    del task_storage[task_id]

    return {"message": "Task deleted successfully"}

if __name__ == "__main__":
    print("Starting VibeVoice TTS Server (Mock)...")
    print("Available voices:")
    for voice_id, voice_name in VOICE_MAP.items():
        print(f"  {voice_id}: {voice_name}")

    uvicorn.run(app, host="0.0.0.0", port=8000)