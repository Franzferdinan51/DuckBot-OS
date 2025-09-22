# VibeVoice TTS Setup Guide

## Overview

DuckBot v4.2 includes a comprehensive VibeVoice TTS integration that provides multi-speaker text-to-speech capabilities. Since the original VibeVoice package is not available via pip, this implementation uses a mock server with alternative TTS systems.

## Features

- **Multi-speaker TTS**: Support for up to 6 different voices
- **Real-time generation**: FastAPI-based server running on localhost:8000
- **Fallback systems**: Multiple TTS engines (Edge TTS, pyttsx3, Coqui TTS)
- **Discord integration**: Full Discord bot commands for voice generation
- **Batch processing**: Generate multiple audio files concurrently
- **Emotional synthesis**: Add emotional modulation to speech
- **Podcast generation**: Create multi-segment audio content

## Quick Start

### 1. Start the VibeVoice Server

```bash
# Method 1: Using the batch file (recommended)
START_VIBEVOICE_SERVER.bat

# Method 2: Using Python directly
python start_vibevoice_server.py
```

The server will start on `http://localhost:8000` with the following endpoints:
- `GET /` - Server info
- `GET /voices` - Available voices
- `POST /generate` - Generate speech
- `GET /status/{task_id}` - Check generation status
- `GET /result/{task_id}` - Download generated audio
- `GET /health` - Health check

### 2. Test the Server

```bash
# Check server health
curl http://localhost:8000/health

# List available voices
curl http://localhost:8000/voices

# Test generation
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"script": "Hello world!", "speaker_names": ["en-alice"], "cfg_scale": 1.3}'
```

### 3. Use with DuckBot

The VibeVoice integration is automatically available in DuckBot. You can test it with:

```python
import asyncio
from duckbot.integrations.vibevoice_client import vibevoice_integration

async def test():
    # Initialize the integration
    await vibevoice_integration.ensure_initialized()

    # Generate speech
    result = await vibevoice_integration.generate_speech(
        "Hello from DuckBot!",
        speakers=["en-alice", "en-carter"]
    )

    if result["success"]:
        print(f"Audio saved to: {result['audio_path']}")
    else:
        print(f"Generation failed: {result['error']}")

asyncio.run(test())
```

## Available Voices

| Voice ID | Name | Language | Gender |
|----------|------|----------|--------|
| en-alice | en-US-AriaNeural | English | Female |
| en-carter | en-US-GuyNeural | English | Male |
| en-david | en-US-ChristopherNeural | English | Male |
| en-emily | en-US-JennyNeural | English | Female |
| zh-xiaoli | zh-CN-XiaoxiaoNeural | Chinese | Female |
| zh-wang | zh-CN-YunxiNeural | Chinese | Male |

## Discord Commands

The VibeVoice integration includes several Discord commands:

### `/vibevoice`
Generate multi-speaker voice content.

**Parameters:**
- `text`: Text to convert to speech
- `preset`: Voice preset (alice, carter, conversation, debate, podcast, news)
- `speakers`: Custom speaker voices (comma-separated)
- `upload`: Upload audio file to Discord (default: true)

**Examples:**
```
/vibevoice text:"Hello everyone!" preset:alice
/vibevoice text:"Speaker1: Hi! Speaker2: Hello there!" preset:conversation
/vibevoice text:"News announcement" speakers:en-emily,en-carter
```

### `/voice_presets`
Show available voice presets and individual voices.

### `/voice_status`
Check VibeVoice service status and configuration.

### `/voice_help`
Complete guide to using VibeVoice TTS commands.

## Voice Presets

| Preset | Voices | Use Case |
|--------|--------|----------|
| alice | [en-alice] | Single female voice |
| carter | [en-carter] | Single male voice |
| conversation | [en-alice, en-carter] | Balanced dialogue |
| debate | [en-david, en-emily] | Formal discussion |
| podcast | [en-alice, en-carter, en-david] | Multi-voice content |
| news | [en-emily, en-carter] | Professional announcements |

## Configuration

### Environment Variables

```bash
# Enable/disable VibeVoice
ENABLE_VIBEVOICE=true

# Server URL (default: http://localhost:8000)
VIBEVOICE_API_URL=http://localhost:8000

# Discord configuration (in config/discord_config.json)
```

### Discord Configuration

Create or update `config/discord_config.json`:

```json
{
  "features": {
    "vibevoice": {
      "presets": {
        "alice": ["en-alice"],
        "carter": ["en-carter"],
        "conversation": ["en-alice", "en-carter"],
        "debate": ["en-david", "en-emily"],
        "podcast": ["en-alice", "en-carter", "en-david"],
        "news": ["en-emily", "en-carter"]
      },
      "max_text_length": 2000,
      "max_file_size_mb": 8,
      "cleanup_delay_seconds": 300
    }
  },
  "rate_limits": {
    "vibevoice": {
      "max_calls": 10,
      "period": 300
    }
  }
}
```

## Troubleshooting

### Server Won't Start

**Problem:** Server fails to start or dependencies missing

**Solution:**
```bash
# Check Python version
python --version

# Install dependencies
pip install fastapi uvicorn pydantic edge-tts pyttsx3 TTS

# Test TTS systems individually
python -c "import edge_tts; print('Edge TTS OK')"
python -c "import pyttsx3; print('pyttsx3 OK')"
python -c "from TTS.api import TTS; print('Coqui TTS OK')"
```

### Port 8000 Already in Use

**Problem:** Another service is using port 8000

**Solution:**
```bash
# Find what's using the port
netstat -ano | findstr :8000

# Change port in start_vibevoice_server.py
# uvicorn.run(app, host="0.0.0.0", port=8001)  # Change to 8001
```

### VibeVoice Not Available in DuckBot

**Problem:** Integration shows as unavailable

**Solution:**
1. Ensure server is running: `curl http://localhost:8000/health`
2. Check environment variables: `echo %ENABLE_VIBEVOICE%`
3. Verify network connectivity
4. Restart DuckBot after starting server

### Discord Commands Not Working

**Problem:** Discord commands fail or show errors

**Solution:**
1. Check bot permissions in Discord server
2. Verify Discord configuration file
3. Ensure VibeVoice server is running
4. Check Discord bot logs for errors

### Audio Generation Fails

**Problem:** Audio generation fails or produces no output

**Solution:**
1. Check text length (max 2000 characters)
2. Verify speaker names are valid
3. Test with simple text first
4. Check server logs for errors
5. Try different TTS engines

### File Upload Issues

**Problem:** Audio files too large for Discord upload

**Solution:**
1. Keep text under 1000 characters for smaller files
2. Set `upload: false` in command
3. Use file system location provided in response

## Advanced Usage

### Batch Processing

```python
async def batch_generate():
    items = [
        {"text": "Hello", "speakers": ["en-alice"]},
        {"text": "World", "speakers": ["en-carter"]},
        {"text": "How are you?", "speakers": ["en-emily"]}
    ]

    results = await vibevoice_integration.manager.batch_generate(items)
    for result in results:
        if result["success"]:
            print(f"Generated: {result['result']['audio_path']}")
```

### Emotional Speech

```python
async def emotional_speech():
    result = await vibevoice_integration.manager.generate_with_emotion(
        text="I'm so excited to be here!",
        emotion="happy",
        speaker="en-alice",
        intensity=0.8
    )
```

### Podcast Generation

```python
async def create_podcast():
    content = {
        "intro": "Welcome to our tech podcast!",
        "segments": [
            {
                "type": "monologue",
                "speaker": "en-alice",
                "text": "Today we're discussing AI technology.",
                "title": "Introduction"
            },
            {
                "type": "interview",
                "conversation": [
                    {"speaker": "en-alice", "text": "What do you think about AI?"},
                    {"speaker": "en-carter", "text": "It's fascinating!"}
                ],
                "title": "Discussion"
            }
        ],
        "outro": "Thanks for listening!"
    }

    result = await vibevoice_integration.manager.generate_podcast_episode(content)
```

## Architecture

The VibeVoice system consists of:

1. **VibeVoice Server** (`vibevoice_server.py`):
   - FastAPI application providing mock VibeVoice API
   - Multiple TTS engine support with fallbacks
   - Task-based generation system

2. **VibeVoice Client** (`duckbot/integrations/vibevoice_client.py`):
   - Async client for server communication
   - High-level API for speech generation
   - Integration with DuckBot systems

3. **Discord Commands** (`duckbot/agents/vibevoice_commands.py`):
   - Discord slash commands
   - Voice presets and configuration
   - File management and cleanup

4. **Startup Scripts**:
   - `START_VIBEVOICE_SERVER.bat` - Windows batch launcher
   - `start_vibevoice_server.py` - Python startup script

## Performance Notes

- **Generation Time**: Typically 5-30 seconds depending on text length
- **File Size**: ~1-10 MB per minute of audio
- **Concurrent Requests**: Server handles multiple requests simultaneously
- **Memory Usage**: ~500MB base + memory for active generations
- **CPU Usage**: Moderate during generation, minimal when idle

## Security Considerations

- Server runs locally by default (localhost:8000)
- No external API calls for pyttsx3 (offline TTS)
- Edge TTS requires internet connection
- Audio files are stored in temporary directories
- Automatic cleanup after 5 minutes (configurable)

## Future Enhancements

- [ ] Add more TTS engines (Amazon Polly, Google Cloud TTS)
- [ ] Implement audio compression options
- [ ] Add voice cloning capabilities
- [ ] Support for more languages
- [ ] Real-time streaming audio generation
- [ ] Voice effect processing (reverb, pitch shift, etc.)

## Support

For issues and questions:
1. Check server logs: `vibevoice_server.log`
2. Verify DuckBot logs
3. Test server endpoints manually
4. Check network connectivity
5. Review configuration files

---

**Version**: 1.0.0
**Compatible**: DuckBot v4.2+
**License**: Open Source (MIT)