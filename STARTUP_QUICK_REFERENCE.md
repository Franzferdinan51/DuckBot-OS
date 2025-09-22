# DuckBot v4.2 Startup Quick Reference

## 🚀 Main Launcher: `launcher\CONSOLIDATED_DUCKBOT_LAUNCHER.bat`

### Primary Modes
| Option | Service | Port | Access | Purpose |
|--------|---------|------|--------|---------|
| **1** | Ultimate Ecosystem | 8787 | http://localhost:8787 | Complete experience |
| **2** | WebUI Only | 8787 | http://localhost:8787 | Dashboard only |
| **3** | Headless AI | - | - | AI management only |
| **4** | Local Only | 8787 | http://localhost:8787 | Offline with LM Studio |
| **5** | Quick Start | 8787 | http://localhost:8787 | Fast startup |

### Specialized Modes
| Option | Service | Port | Access | Purpose |
|--------|---------|------|--------|---------|
| **6** | System Test | - | - | Comprehensive testing |
| **7** | Monitoring | 8789 | http://localhost:8789 | System metrics |
| **8** | AI Chat | - | - | Interactive assistant |
| **9** | VibeVoice TTS | 8000 | http://localhost:8000 | Text-to-speech |
| **10** | Voice Chat | 8001 | http://localhost:8001 | Real-time voice |

### Management
| Option | Action | Purpose |
|--------|--------|---------|
| **A** | All Services | Start everything |
| **I** | Install | Auto-install dependencies |
| **U** | Update | Update all components |
| **D** | Doctor | System diagnostics |
| **S** | Status | Quick system check |
| **K** | Kill | Stop all processes |
| **C** | Config | Configure settings |
| **H** | Help | Show help |
| **Q** | Quit | Exit launcher |

## 🎯 Individual Starters

### Web Services
| File | Service | Port | Access |
|------|---------|------|--------|
| `START_WEBUI.bat` | WebUI Dashboard | 8787 | http://localhost:8787 |
| `START_MONITORING.bat` | System Monitor | 8789 | http://localhost:8789 |

### AI Services
| File | Service | Purpose |
|------|---------|---------|
| `START_HEADLESS.bat` | Headless AI | AI management only |
| `START_CHAT.bat` | AI Assistant | Interactive chat |

### Voice Services
| File | Service | Port | Access |
|------|---------|------|--------|
| `START_VIBEVOICE_SERVER.bat` | VibeVoice TTS | 8000 | http://localhost:8000 |
| `start_realtime_voicechat_enhanced.bat` | Voice Chat | 8001 | http://localhost:8001 |
| `START_DISCORD_BOT.bat` | Discord Bot | - | Discord integration |

### Utilities
| File | Purpose |
|------|---------|
| `START_ALL_SERVICES.bat` | Start everything |
| `START_KILL.bat` | Stop all services |
| `START_INSTALL.bat` | Install dependencies |
| `START_DOCTOR.bat` | System diagnostics |

## 🔌 Port Summary

| Port | Service | Purpose |
|------|---------|---------|
| **8787** | WebUI Dashboard | Main interface |
| **8789** | System Monitor | Performance metrics |
| **8000** | VibeVoice TTS | Text-to-speech API |
| **8001** | Voice Chat | Real-time voice chat |

## 🎙️ Voice Services Quick Start

### VibeVoice TTS
```bash
# Start server
START_VIBEVOICE_SERVER.bat

# Test API
curl http://localhost:8000/health
curl http://localhost:8000/voices

# Convert speech
curl -X POST http://localhost:8000/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello DuckBot!"}'
```

### Realtime Voice Chat
```bash
# Start server
start_realtime_voicechat_enhanced.bat

# Access in browser
open http://localhost:8001

# WebSocket connection
ws://localhost:8001/ws/{session_id}
```

## 🛠️ Common Commands

### System Status
```bash
# Check ports
netstat -ano | findstr :8787
netstat -ano | findstr :8000

# Check processes
tasklist | findstr python
```

### Quick Fixes
```bash
# Free all ports
START_KILL.bat

# Install dependencies
START_INSTALL.bat

# System diagnostics
START_DOCTOR.bat
```

## 🚨 Troubleshooting

### Issue: Port conflicts
**Fix**: Run `START_KILL.bat` to free all ports

### Issue: Python not found
**Fix**: Install Python 3.8+ and add to PATH

### Issue: Missing dependencies
**Fix**: Run `START_INSTALL.bat` or option I in launcher

### Issue: Services not accessible
**Fix**: Check firewall settings and port availability

## 📋 Service Dependencies

| Service | Dependencies | Notes |
|---------|--------------|-------|
| WebUI | Basic Python | No extra dependencies |
| VibeVoice | edge-tts, pyttsx3 | Audio libraries |
| Voice Chat | microphone access | Browser permissions |
| Discord Bot | DISCORD_TOKEN | .env configuration |

## 🔧 Configuration Files

| File | Purpose |
|------|---------|
| `.env` | Environment variables |
| `ai_config.json` | AI provider settings |
| `ecosystem_config.yaml` | Service configuration |
| `requirements.txt` | Python dependencies |

---

**Quick Tip**: For complete experience, use **Option 1** in main launcher or run `START_ALL_SERVICES.bat`