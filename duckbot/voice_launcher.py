#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DuckBot Voice-Controlled Launcher
AI-powered voice commands for launching DuckBot components
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import re

# Try to import speech recognition and VibeVoice
try:
    import speech_recognition as sr
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False
    print("Warning: speech_recognition not available. Install: pip install SpeechRecognition")

try:
    from duckbot.integrations.vibevoice_client import VibeVoiceClient
    VIBEVOICE_AVAILABLE = True
except ImportError:
    VIBEVOICE_AVAILABLE = False
    print("Warning: VibeVoice not available")

# Import from our AI startup interface
try:
    from duckbot.ai_startup_interface import AIStartupInterface, StartupMode
    STARTUP_AVAILABLE = True
except ImportError:
    STARTUP_AVAILABLE = False
    print("Warning: AI startup interface not available")

logger = logging.getLogger(__name__)

class VoiceLauncher:
    """Voice-controlled launcher with AI integration"""

    def __init__(self):
        self.startup_interface = AIStartupInterface() if STARTUP_AVAILABLE else None
        self.vibevoice = VibeVoiceClient() if VIBEVOICE_AVAILABLE else None
        self.recognizer = sr.Recognizer() if SPEECH_AVAILABLE else None
        self.microphone = sr.Microphone() if SPEECH_AVAILABLE else None
        self.is_listening = False
        self.command_history = []

        # Voice command patterns
        self.command_patterns = {
            'launch': [
                r'launch\s+(.+)',
                r'start\s+(.+)',
                r'run\s+(.+)',
                r'begin\s+(.+)',
                r'activate\s+(.+)'
            ],
            'status': [
                r'status',
                r'how are you',
                r'what\'s running',
                r'system status',
                r'check status'
            ],
            'list': [
                r'list\s+modes',
                r'show\s+modes',
                r'what\s+can\s+i\s+launch',
                r'available\s+modes',
                r'help'
            ],
            'recommend': [
                r'recommend',
                r'what\s+should\s+i\s+run',
                r'suggest',
                r'best\s+mode',
                r'what\s+do\s+you\s+recommend'
            ],
            'stop': [
                r'stop\s+listening',
                r'deactivate',
                r'go to sleep',
                r'quiet',
                'stop'
            ],
            'setup': [
                r'setup\s+api',
                r'configure\s+keys',
                r'api\s+setup',
                r'add\s+keys',
                r'configure'
            ]
        }

    def calibrate_microphone(self):
        """Calibrate microphone for ambient noise"""
        if not SPEECH_AVAILABLE:
            print("❌ Speech recognition not available")
            return False

        try:
            print("🎤 Calibrating microphone for ambient noise...")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
            print("✅ Microphone calibrated")
            return True
        except Exception as e:
            print(f"❌ Error calibrating microphone: {e}")
            return False

    def listen_for_command(self) -> Optional[str]:
        """Listen for voice command"""
        if not SPEECH_AVAILABLE or not self.microphone:
            return None

        try:
            with self.microphone as source:
                print("🎤 Listening...")
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)

            print("🧠 Processing...")
            try:
                # Try Google Speech Recognition first
                command = self.recognizer.recognize_google(audio).lower()
                print(f"📝 Heard: {command}")
                return command
            except sr.UnknownValueError:
                print("❌ Could not understand audio")
                return None
            except sr.RequestError as e:
                print(f"❌ Speech recognition error: {e}")
                return None

        except sr.WaitTimeoutError:
            print("⏰ Listening timeout")
            return None
        except Exception as e:
            print(f"❌ Error listening: {e}")
            return None

    def parse_command(self, command: str) -> Dict[str, Any]:
        """Parse voice command and extract intent"""
        command = command.lower().strip()

        # Check each command type
        for intent, patterns in self.command_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, command)
                if match:
                    result = {'intent': intent}
                    if match.groups():
                        result['target'] = match.group(1).strip()
                    return result

        return {'intent': 'unknown', 'raw': command}

    def find_mode_by_voice_command(self, target: str) -> Optional[StartupMode]:
        """Find startup mode by voice command"""
        if not self.startup_interface:
            return None

        target = target.lower().strip()

        # Direct ID matching
        mode = self.startup_interface.get_mode_by_id(target)
        if mode:
            return mode

        # Fuzzy matching by name
        for mode in self.startup_interface.startup_modes:
            if target in mode.name.lower() or target in mode.description.lower():
                return mode

        # Keyword matching
        keywords = {
            'ai': ['ai enhanced', 'ai', 'ultimate', 'complete'],
            'webui': ['webui', 'dashboard', 'web', 'interface'],
            'local': ['local', 'privacy', 'offline'],
            'automation': ['bytebot', 'automation', 'desktop'],
            'gui': ['ui tars', 'gui', 'visual', 'interface'],
            'agent': ['archon', 'multi', 'agent'],
            'communication': ['livekit', 'communication', 'webrtc'],
            'workflow': ['n8n', 'workflow', 'automation'],
            'learning': ['learning', 'ai', 'adaptive'],
            'mcp': ['mcp', 'protocol', 'server'],
            'terminal': ['charm', 'terminal', 'interface'],
            'monitor': ['monitor', 'ai', 'system'],
            'development': ['development', 'dev', 'coding']
        }

        for category, keywords_list in keywords.items():
            if any(keyword in target for keyword in keywords_list):
                for mode in self.startup_interface.startup_modes:
                    if category in mode.name.lower() or category in mode.description.lower():
                        return mode

        return None

    def speak_response(self, text: str):
        """Speak response using VibeVoice or fallback"""
        if VIBEVOICE_AVAILABLE and self.vibevoice:
            try:
                asyncio.run(self.vibevoice.speak(text))
                return
            except Exception as e:
                print(f"VibeVoice error: {e}")

        # Fallback to console
        print(f"🤖 Assistant: {text}")

    def handle_command(self, command_data: Dict[str, Any]):
        """Handle parsed voice command"""
        intent = command_data.get('intent')
        target = command_data.get('target')

        if intent == 'launch':
            if not target:
                self.speak_response("What would you like me to launch?")
                return

            mode = self.find_mode_by_voice_command(target)
            if mode:
                # Check API requirements
                if self.startup_interface:
                    requirements = self.startup_interface.check_api_requirements(mode)
                    missing_apis = [api for api, available in requirements.items() if not available]

                    if missing_apis:
                        self.speak_response(f"I need {', '.join(missing_apis)} API keys to launch {mode.name}. Please set them up first.")
                        return

                self.speak_response(f"Launching {mode.name}...")
                if self.startup_interface:
                    self.startup_interface.launch_mode(mode.id)
            else:
                self.speak_response(f"I couldn't find a mode matching '{target}'. Available modes are:")
                if self.startup_interface:
                    for mode in self.startup_interface.startup_modes[:5]:  # List first 5
                        self.speak_response(f"- {mode.name}")

        elif intent == 'status':
            self.speak_response("System status check in progress...")
            if self.startup_interface:
                available_apis = []
                if self.startup_interface.api_keys.gemini_api_key:
                    available_apis.append("Gemini")
                if self.startup_interface.api_keys.openrouter_api_key:
                    available_apis.append("OpenRouter")
                if self.startup_interface.api_keys.zai_api_key:
                    available_apis.append("Z.ai")

                if available_apis:
                    self.speak_response(f"System ready with {', '.join(available_apis)} APIs configured.")
                else:
                    self.speak_response("System ready, but no API keys configured.")

        elif intent == 'list':
            self.speak_response("Available launch modes:")
            if self.startup_interface:
                for mode in self.startup_interface.startup_modes:
                    self.speak_response(f"- {mode.name}")

        elif intent == 'recommend':
            self.speak_response("Based on your configuration, I recommend:")
            if self.startup_interface:
                # Simple recommendation logic
                if self.startup_interface.api_keys.gemini_api_key and self.startup_interface.api_keys.openrouter_api_key:
                    self.speak_response("Ultimate Complete AI System for full functionality")
                elif self.startup_interface.api_keys.gemini_api_key:
                    self.speak_response("ByteBot for desktop automation or AI Learning System")
                elif self.startup_interface.api_keys.openrouter_api_key:
                    self.speak_response("Archon Multi-Agent System or AI Enhanced WebUI")
                else:
                    self.speak_response("Please setup API keys first for AI-powered recommendations")

        elif intent == 'stop':
            self.speak_response("Voice control deactivated. Say 'start listening' to activate again.")
            self.is_listening = False

        elif intent == 'setup':
            self.speak_response("API key setup requires the interface. Please use the web launcher or terminal interface.")

        elif intent == 'unknown':
            self.speak_response("I didn't understand that command. Try 'launch', 'status', 'list', 'recommend', or 'stop'.")

        # Add to command history
        self.command_history.append({
            'command': command_data,
            'timestamp': asyncio.get_event_loop().time() if asyncio.get_event_loop().is_running() else None
        })

    def start_voice_control(self):
        """Start voice control loop"""
        if not SPEECH_AVAILABLE:
            print("❌ Voice control requires speech recognition library")
            print("Install: pip install SpeechRecognition")
            return

        if not self.calibrate_microphone():
            return

        print("🎤 Voice Control Started!")
        print("Say 'start listening' to activate, then give commands like:")
        print("  - 'Launch AI Enhanced WebUI'")
        print("  - 'What's the status?'")
        print("  - 'Show available modes'")
        print("  - 'What do you recommend?'")
        print("  - 'Stop listening'")

        # Initial activation
        self.speak_response("Voice control ready. Say 'start listening' to activate.")

        while True:
            try:
                command = self.listen_for_command()

                if command:
                    if "start listening" in command or "activate" in command:
                        self.is_listening = True
                        self.speak_response("Voice control activated. I'm listening for commands.")
                    elif self.is_listening:
                        command_data = self.parse_command(command)
                        self.handle_command(command_data)
                    else:
                        print("🔒 Voice control not active. Say 'start listening' to activate.")

            except KeyboardInterrupt:
                print("\n👋 Voice control stopped.")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    def start_listening_mode(self):
        """Start continuous listening mode"""
        if not SPEECH_AVAILABLE:
            print("❌ Speech recognition not available")
            return

        if not self.calibrate_microphone():
            return

        self.is_listening = True
        self.speak_response("Continuous listening mode activated. I'm always listening now.")

        while self.is_listening:
            try:
                command = self.listen_for_command()
                if command:
                    command_data = self.parse_command(command)
                    self.handle_command(command_data)

                    # Check for deactivation
                    if command_data.get('intent') == 'stop':
                        break

            except KeyboardInterrupt:
                print("\n👋 Voice control stopped.")
                self.is_listening = False
                break
            except Exception as e:
                print(f"❌ Error: {e}")

async def main():
    """Main entry point"""
    launcher = VoiceLauncher()

    print("🎤 DuckBot Voice-Controlled Launcher")
    print("1. Continuous listening mode")
    print("2. Command mode (say 'start listening')")
    print("3. Exit")

    choice = input("Select mode (1-3): ").strip()

    if choice == "1":
        launcher.start_listening_mode()
    elif choice == "2":
        launcher.start_voice_control()
    else:
        print("👋 Goodbye!")

if __name__ == "__main__":
    asyncio.run(main())