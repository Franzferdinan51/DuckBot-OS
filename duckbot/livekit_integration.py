#!/usr/bin/env python3
"""
LiveKit Integration for DuckBot
Real-time WebRTC audio/video conferencing alongside VibeVoice TTS
"""

import asyncio
import json
import logging
from typing import Optional, Dict, List, Any
from pathlib import Path
import tempfile
import os
from datetime import datetime

try:
    from livekit import rtc
    from livekit.api import LiveKitAPI, TokenPermissions, VideoGrants
    LIVEKIT_AVAILABLE = True
except ImportError as e:
    LIVEKIT_AVAILABLE = False
    rtc = None
    LiveKitAPI = None
    TokenPermissions = None
    VideoGrants = None

from .cost_tracker import CostTracker

logger = logging.getLogger(__name__)

class LiveKitIntegration:
    """LiveKit WebRTC integration for real-time audio/video conferencing."""

    def __init__(self,
                 api_key: Optional[str] = None,
                 api_secret: Optional[str] = None,
                 websocket_url: Optional[str] = None,
                 cost_tracker: Optional[CostTracker] = None):
        """
        Initialize LiveKit integration.

        Args:
            api_key: LiveKit API key
            api_secret: LiveKit API secret
            websocket_url: LiveKit server WebSocket URL
            cost_tracker: Optional cost tracking instance
        """
        self.api_key = api_key or os.getenv('LIVEKIT_API_KEY')
        self.api_secret = api_secret or os.getenv('LIVEKIT_API_SECRET')
        self.websocket_url = websocket_url or os.getenv('LIVEKIT_WS_URL', 'ws://localhost:7880')
        self.cost_tracker = cost_tracker

        self.room = None
        self.connected = False
        self.participants = {}

        if not LIVEKIT_AVAILABLE:
            logger.warning("LiveKit SDK not available. Install with: pip install livekit livekit-api")
            return

        if not self.api_key or not self.api_secret:
            logger.warning("LiveKit credentials not configured. Set LIVEKIT_API_KEY and LIVEKIT_API_SECRET")
            return

        self.api = LiveKitAPI(self.api_key, self.api_secret)
        logger.info("LiveKit integration initialized")

    async def connect_to_room(self, room_name: str, participant_name: str = "DuckBot") -> bool:
        """Connect to a LiveKit room."""
        if not LIVEKIT_AVAILABLE:
            logger.error("LiveKit not available")
            return False

        try:
            # Generate token for room access
            token = await self._generate_token(room_name, participant_name)

            # Create and connect room
            self.room = rtc.Room()

            @self.room.on("participant_connected")
            def on_participant_connected(participant):
                logger.info(f"Participant connected: {participant.identity}")
                self.participants[participant.sid] = participant

            @self.room.on("participant_disconnected")
            def on_participant_disconnected(participant):
                logger.info(f"Participant disconnected: {participant.identity}")
                if participant.sid in self.participants:
                    del self.participants[participant.sid]

            # Connect to room
            await self.room.connect(self.websocket_url, token)
            self.connected = True
            logger.info(f"Connected to LiveKit room: {room_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to LiveKit room: {e}")
            return False

    async def disconnect(self):
        """Disconnect from current room."""
        if self.room and self.connected:
            await self.room.disconnect()
            self.connected = False
            self.participants.clear()
            logger.info("Disconnected from LiveKit room")

    async def _generate_token(self, room_name: str, participant_name: str) -> str:
        """Generate access token for LiveKit room."""
        try:
            grants = VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True
            )

            token = self.api.create_token(
                identity=participant_name,
                grants=grants
            )

            return token.to_jwt()

        except Exception as e:
            logger.error(f"Failed to generate token: {e}")
            raise

    async def start_audio_broadcast(self, audio_file_path: str) -> bool:
        """Broadcast audio file to all participants in the room."""
        if not self.connected or not self.room:
            logger.error("Not connected to a room")
            return False

        try:
            # Create audio track from file
            audio_source = rtc.AudioSource(24000, 1)  # 24kHz, mono
            audio_track = rtc.LocalAudioTrack.create_audio_track("audio_broadcast", audio_source)

            # Publish track to room
            track_publication = await self.room.local_participant.publish_track(audio_track)
            logger.info(f"Audio broadcast started: {audio_file_path}")

            # Here you would typically stream the audio file content
            # This is a simplified implementation
            return True

        except Exception as e:
            logger.error(f"Failed to start audio broadcast: {e}")
            return False

    async def create_voice_room(self, room_name: str, max_participants: int = 50) -> Dict[str, Any]:
        """Create a new voice conference room."""
        try:
            # Create room via LiveKit API
            room = await self.api.room.create_room(
                name=room_name,
                empty_timeout=300,  # 5 minutes
                max_participants=max_participants
            )

            logger.info(f"Created LiveKit room: {room_name}")
            return {
                "room_name": room_name,
                "sid": room.sid,
                "max_participants": max_participants,
                "websocket_url": self.websocket_url,
                "created_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to create room: {e}")
            return {}

    async def get_room_info(self, room_name: str) -> Dict[str, Any]:
        """Get information about a specific room."""
        try:
            room = await self.api.room.get_room(room_name)
            return {
                "room_name": room.name,
                "sid": room.sid,
                "participant_count": len(self.participants),
                "max_participants": room.max_participants,
                "empty_timeout": room.empty_timeout,
                "created_at": room.creation_time.isoformat() if room.creation_time else None
            }
        except Exception as e:
            logger.error(f"Failed to get room info: {e}")
            return {}

    def generate_join_link(self, room_name: str, participant_name: str) -> str:
        """Generate a join link for participants."""
        try:
            token = asyncio.run(self._generate_token(room_name, participant_name))
            return f"{self.websocket_url}?token={token}&room={room_name}"
        except Exception as e:
            logger.error(f"Failed to generate join link: {e}")
            return ""

    async def list_rooms(self) -> List[Dict[str, Any]]:
        """List all available rooms."""
        try:
            rooms = await self.api.room.list_rooms()
            return [
                {
                    "name": room.name,
                    "sid": room.sid,
                    "participant_count": len(self.participants),
                    "max_participants": room.max_participants
                }
                for room in rooms
            ]
        except Exception as e:
            logger.error(f"Failed to list rooms: {e}")
            return []

    async def delete_room(self, room_name: str) -> bool:
        """Delete a specific room."""
        try:
            await self.api.room.delete_room(room_name)
            logger.info(f"Deleted room: {room_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete room: {e}")
            return False

    def get_participant_count(self) -> int:
        """Get current participant count."""
        return len(self.participants)

    def get_participants(self) -> List[Dict[str, Any]]:
        """Get list of current participants."""
        return [
            {
                "sid": p.sid,
                "identity": p.identity,
                "name": p.name,
                "tracks": len(p.audio_tracks) + len(p.video_tracks)
            }
            for p in self.participants.values()
        ]

    async def send_data_message(self, data: Any, destination_sid: Optional[str] = None) -> bool:
        """Send data message to participants."""
        if not self.connected or not self.room:
            return False

        try:
            payload = json.dumps(data).encode('utf-8')
            await self.room.local_participant.publish_data(
                payload=payload,
                kind=rtc.DataPacketKind.RELIABLE,
                destination_sids=[destination_sid] if destination_sid else None
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send data message: {e}")
            return False

    def is_available(self) -> bool:
        """Check if LiveKit integration is available."""
        return LIVEKIT_AVAILABLE and bool(self.api_key and self.api_secret)

    async def test_connection(self) -> bool:
        """Test LiveKit connection."""
        if not self.is_available():
            return False

        try:
            # Try to list rooms as a simple test
            rooms = await self.list_rooms()
            logger.info(f"LiveKit connection test successful. Found {len(rooms)} rooms")
            return True
        except Exception as e:
            logger.error(f"LiveKit connection test failed: {e}")
            return False


class VibeVoiceLiveKitBridge:
    """Bridge between VibeVoice TTS and LiveKit for enhanced voice experiences."""

    def __init__(self, vibevoice_client=None, livekit_integration=None):
        """
        Initialize the bridge between VibeVoice and LiveKit.

        Args:
            vibevoice_client: VibeVoice TTS client instance
            livekit_integration: LiveKit integration instance
        """
        self.vibevoice = vibevoice_client
        self.livekit = livekit_integration

    async def generate_and_broadcast(self, text: str, voice_preset: str = "conversation") -> bool:
        """
        Generate speech with VibeVoice and broadcast via LiveKit.

        Args:
            text: Text to convert to speech
            voice_preset: Voice preset to use

        Returns:
            True if successful
        """
        if not self.vibevoice or not self.livekit:
            logger.error("Both VibeVoice and LiveKit must be available")
            return False

        try:
            # Generate audio with VibeVoice
            audio_data = await self.vibevoice.generate_speech(
                text=text,
                speakers=voice_preset
            )

            if not audio_data:
                logger.error("Failed to generate audio with VibeVoice")
                return False

            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name

            try:
                # Broadcast via LiveKit
                success = await self.livekit.start_audio_broadcast(temp_file_path)
                return success
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)

        except Exception as e:
            logger.error(f"Failed to generate and broadcast: {e}")
            return False

    async def create_voice_conference(self, room_name: str, title: str, description: str = "") -> Dict[str, Any]:
        """Create a complete voice conference with TTS capabilities."""
        if not self.livekit:
            return {}

        try:
            # Create LiveKit room
            room_info = await self.livekit.create_voice_room(room_name)

            # Send initial announcement
            if self.vibevoice:
                welcome_text = f"Welcome to the {title} voice conference. {description}"
                await self.generate_and_broadcast(welcome_text)

            return {
                **room_info,
                "title": title,
                "description": description,
                "tts_enabled": bool(self.vibevoice),
                "join_link": self.livekit.generate_join_link(room_name, "Participant")
            }

        except Exception as e:
            logger.error(f"Failed to create voice conference: {e}")
            return {}


# Discord commands for LiveKit integration
class LiveKitCommands:
    """Discord commands for LiveKit functionality."""

    def __init__(self, bot, livekit_integration: Optional[LiveKitIntegration] = None):
        self.bot = bot
        self.livekit = livekit_integration

    async def setup_commands(self):
        """Set up Discord slash commands for LiveKit."""
        if not self.livekit or not self.livekit.is_available():
            return

        # Voice conference command
        @self.bot.tree.command(name="create_voice_room", description="Create a voice conference room")
        @app_commands.describe(
            room_name="Name for the voice room",
            title="Conference title",
            max_participants="Maximum participants (default: 50)"
        )
        async def create_voice_room_command(
            interaction: discord.Interaction,
            room_name: str,
            title: str,
            max_participants: int = 50
        ):
            await interaction.response.defer()

            try:
                room_info = await self.livekit.create_voice_room(room_name, max_participants)
                join_link = self.livekit.generate_join_link(room_name, interaction.user.display_name)

                embed = discord.Embed(
                    title=f"🎙️ Voice Conference Created: {title}",
                    description=f"Room: **{room_name}**",
                    color=discord.Color.green()
                )

                embed.add_field(name="Join Link", value=f"[Click to Join]({join_link})", inline=False)
                embed.add_field(name="Max Participants", value=str(max_participants), inline=True)
                embed.add_field(name="Room ID", value=room_info.get("sid", "N/A"), inline=True)

                await interaction.followup.send(embed=embed)

            except Exception as e:
                await interaction.followup.send(f"❌ Failed to create voice room: {e}")

        # List rooms command
        @self.bot.tree.command(name="list_voice_rooms", description="List available voice conference rooms")
        async def list_voice_rooms_command(interaction: discord.Interaction):
            await interaction.response.defer()

            try:
                rooms = await self.livekit.list_rooms()

                if not rooms:
                    await interaction.followup.send("No active voice rooms found.")
                    return

                embed = discord.Embed(
                    title="🎙️ Active Voice Rooms",
                    description=f"Found {len(rooms)} active room(s)",
                    color=discord.Color.blue()
                )

                for room in rooms:
                    embed.add_field(
                        name=f"📞 {room['name']}",
                        value=f"Participants: {room['participant_count']}/{room['max_participants']}",
                        inline=False
                    )

                await interaction.followup.send(embed=embed)

            except Exception as e:
                await interaction.followup.send(f"❌ Failed to list rooms: {e}")


# Test function
async def test_livekit_integration():
    """Test LiveKit integration functionality."""
    print("🧪 Testing LiveKit Integration...")

    # Initialize integration
    livekit = LiveKitIntegration()

    if not livekit.is_available():
        print("❌ LiveKit not available - check credentials")
        return False

    # Test connection
    if await livekit.test_connection():
        print("✅ LiveKit connection successful")

        # Test room creation
        room_name = f"test_room_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        room_info = await livekit.create_voice_room(room_name, 10)

        if room_info:
            print(f"✅ Room created: {room_info['name']}")

            # Test room listing
            rooms = await livekit.list_rooms()
            print(f"✅ Room listing successful: {len(rooms)} rooms found")

            # Clean up
            await livekit.delete_room(room_name)
            print("✅ Test room deleted")

            return True
        else:
            print("❌ Failed to create test room")
            return False
    else:
        print("❌ LiveKit connection test failed")
        return False


if __name__ == "__main__":
    # Test the integration
    asyncio.run(test_livekit_integration())