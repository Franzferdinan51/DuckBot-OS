"""
VibeVoice Discord Bot Commands
Integrates Microsoft VibeVoice TTS with DuckBot Discord functionality
"""
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
import tempfile

from .vibevoice_client import VibeVoiceManager
from .cost_tracker import CostTracker

logger = logging.getLogger(__name__)

class VibeVoiceCommands(commands.Cog):
    """Discord commands for VibeVoice TTS functionality."""
    
    def __init__(self, bot: commands.Bot, cost_tracker: Optional[CostTracker] = None):
        self.bot = bot
        self.cost_tracker = cost_tracker
        self.vibevoice = VibeVoiceManager(cost_tracker)
        self.voice_cache = {}  # Cache for generated voice files
        
        # Voice presets for easy selection
        self.voice_presets = {
            "alice": ["en-alice"],
            "carter": ["en-carter"],
            "conversation": ["en-alice", "en-carter"],
            "debate": ["en-david", "en-emily"],
            "podcast": ["en-alice", "en-carter", "en-david"],
            "news": ["en-emily", "en-carter"]
        }
    
    async def cog_load(self):
        """Initialize VibeVoice when cog loads."""
        try:
            initialized = await self.vibevoice.initialize()
            if initialized:
                logger.info("VibeVoice commands loaded successfully")
            else:
                logger.warning("VibeVoice not available - commands will show error")
        except Exception as e:
            logger.error(f"Failed to initialize VibeVoice commands: {e}")
    
    @app_commands.command(name="vibevoice", description="Generate multi-speaker voice content using VibeVoice TTS")
    @app_commands.describe(
        text="Text to convert to speech (can include Speaker1:, Speaker2: labels)",
        preset="Voice preset: alice, carter, conversation, debate, podcast, news",
        speakers="Custom speaker voices (comma-separated): en-alice,en-carter",
        upload="Upload audio file to Discord (default: True)"
    )
    async def vibevoice_command(self, 
                               interaction: discord.Interaction,
                               text: str,
                               preset: str = "conversation",
                               speakers: Optional[str] = None,
                               upload: bool = True):
        """Generate voice content using VibeVoice TTS."""
        
        await interaction.response.defer(thinking=True)
        
        try:
            # Check if VibeVoice is available
            if not self.vibevoice.is_available():
                embed = discord.Embed(
                    title="🚫 VibeVoice Unavailable",
                    description="VibeVoice TTS service is not available. Please check the server status.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Validate text length
            if len(text) > 2000:
                embed = discord.Embed(
                    title="❌ Text Too Long",
                    description="Text must be 2000 characters or less for optimal generation.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Determine speakers
            if speakers:
                speaker_list = [s.strip() for s in speakers.split(',')]
            else:
                speaker_list = self.voice_presets.get(preset, ["en-alice", "en-carter"])
            
            # Generate initial response
            embed = discord.Embed(
                title="🎤 VibeVoice Generation",
                description="Generating multi-speaker voice content...",
                color=discord.Color.blue()
            )
            embed.add_field(name="Text Length", value=f"{len(text)} characters", inline=True)
            embed.add_field(name="Speakers", value=f"{len(speaker_list)} voices", inline=True)
            embed.add_field(name="Preset", value=preset, inline=True)
            
            await interaction.followup.send(embed=embed)
            
            # Generate voice content
            audio_path = await self.vibevoice.generate_voice_content(
                content=text,
                speakers=speaker_list,
                style="conversational"
            )
            
            if audio_path and os.path.exists(audio_path):
                # Success - prepare final embed
                file_size = os.path.getsize(audio_path) / (1024 * 1024)  # MB
                
                embed = discord.Embed(
                    title="✅ VibeVoice Generated",
                    description="Multi-speaker voice content generated successfully!",
                    color=discord.Color.green()
                )
                embed.add_field(name="File Size", value=f"{file_size:.2f} MB", inline=True)
                embed.add_field(name="Speakers Used", value=", ".join(speaker_list), inline=True)
                embed.add_field(name="Generation Time", value="~30-60 seconds", inline=True)
                
                # Upload file if requested and within Discord limits (8MB for most servers)
                if upload and file_size < 8:
                    try:
                        file = discord.File(audio_path, filename=f"vibevoice_{interaction.id}.wav")
                        await interaction.followup.send(embed=embed, file=file)
                    except Exception as e:
                        embed.add_field(name="Upload Error", value=f"Could not upload: {str(e)[:100]}", inline=False)
                        await interaction.followup.send(embed=embed)
                else:
                    # File too large or upload disabled
                    if file_size >= 8:
                        embed.add_field(name="File Note", value="File too large to upload (8MB limit)", inline=False)
                    else:
                        embed.add_field(name="File Location", value=f"Saved to: `{audio_path}`", inline=False)
                    
                    await interaction.followup.send(embed=embed)
                
                # Clean up file after some time (optional)
                asyncio.create_task(self._cleanup_file(audio_path, delay=300))  # 5 minutes
                
            else:
                # Generation failed
                embed = discord.Embed(
                    title="❌ Generation Failed",
                    description="VibeVoice generation failed. Please try again or check the text format.",
                    color=discord.Color.red()
                )
                embed.add_field(
                    name="Tips",
                    value="• Use clear speaker labels (Speaker1:, Speaker2:)\n• Keep text under 2000 characters\n• Ensure VibeVoice server is running",
                    inline=False
                )
                await interaction.followup.send(embed=embed)
        
        except Exception as e:
            logger.error(f"VibeVoice command error: {e}")
            embed = discord.Embed(
                title="🚫 Error",
                description=f"An error occurred: {str(e)[:200]}",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="voice_presets", description="Show available VibeVoice presets and voices")
    async def voice_presets_command(self, interaction: discord.Interaction):
        """Show available voice presets and individual voices."""
        
        embed = discord.Embed(
            title="🎭 VibeVoice Presets & Voices",
            description="Available voice configurations for multi-speaker TTS",
            color=discord.Color.blue()
        )
        
        # Show presets
        preset_text = ""
        for preset, voices in self.voice_presets.items():
            preset_text += f"**{preset}**: {', '.join(voices)}\n"
        
        embed.add_field(
            name="🎯 Voice Presets",
            value=preset_text,
            inline=False
        )
        
        # Show individual voices
        available_voices = self.vibevoice.get_available_voices()
        embed.add_field(
            name="🎤 Individual Voices",
            value=", ".join(available_voices),
            inline=False
        )
        
        # Usage examples
        embed.add_field(
            name="📝 Usage Examples",
            value=(
                "```\n"
                "/vibevoice text:\"Hello world!\" preset:alice\n"
                "/vibevoice text:\"Speaker1: Hi there! Speaker2: Hello!\" preset:conversation\n"
                "/vibevoice text:\"News content\" speakers:en-emily,en-carter\n"
                "```"
            ),
            inline=False
        )
        
        embed.add_field(
            name="💡 Tips",
            value=(
                "• Use `Speaker1:`, `Speaker2:` labels in text\n"
                "• Conversation preset works great for dialogues\n"
                "• News preset is optimized for announcements"
            ),
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="voice_status", description="Check VibeVoice TTS service status")
    async def voice_status_command(self, interaction: discord.Interaction):
        """Check VibeVoice service status and configuration."""
        
        await interaction.response.defer()
        
        embed = discord.Embed(
            title="🔍 VibeVoice Status",
            color=discord.Color.blue()
        )
        
        try:
            # Check if service is available
            is_available = self.vibevoice.is_available()
            
            embed.add_field(
                name="Service Status",
                value="🟢 Available" if is_available else "🔴 Unavailable",
                inline=True
            )
            
            # Get API URL
            api_url = self.vibevoice.api_url
            embed.add_field(
                name="API Endpoint",
                value=api_url,
                inline=True
            )
            
            # Check enabled status
            enabled = self.vibevoice.enabled
            embed.add_field(
                name="Configuration",
                value="🟢 Enabled" if enabled else "🔴 Disabled",
                inline=True
            )
            
            if is_available:
                # Test connection
                async with self.vibevoice.client:
                    connected = await self.vibevoice.client.test_connection()
                    embed.add_field(
                        name="Connection Test",
                        value="🟢 Connected" if connected else "🔴 Failed",
                        inline=True
                    )
                    
                    # Get available voices
                    voices_data = await self.vibevoice.client.get_available_voices()
                    voice_count = len(voices_data.get("voices", []))
                    embed.add_field(
                        name="Available Voices",
                        value=f"{voice_count} voices",
                        inline=True
                    )
            
            # Service info
            embed.add_field(
                name="About VibeVoice",
                value="Microsoft's open-source multi-speaker TTS\n• Supports up to 90 minutes of speech\n• 4 distinct speakers\n• Free to use",
                inline=False
            )
            
        except Exception as e:
            embed.add_field(
                name="Error",
                value=f"Status check failed: {str(e)[:100]}",
                inline=False
            )
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="voice_help", description="Complete guide to using VibeVoice TTS commands")
    async def voice_help_command(self, interaction: discord.Interaction):
        """Comprehensive help for VibeVoice commands."""
        
        embed = discord.Embed(
            title="📖 VibeVoice TTS Guide",
            description="Complete guide to multi-speaker text-to-speech",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="🎤 Main Command: /vibevoice",
            value=(
                "Convert text to multi-speaker speech\n"
                "• **text**: Your content to convert\n"
                "• **preset**: Voice combination (conversation, debate, etc.)\n"
                "• **speakers**: Custom voice selection\n"
                "• **upload**: Auto-upload to Discord (default: true)"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🎯 Quick Examples",
            value=(
                "```\n"
                "Basic: /vibevoice text:\"Hello everyone!\"\n"
                "Dialogue: /vibevoice text:\"Alice: Hi! Bob: Hello there!\"\n"
                "Custom: /vibevoice speakers:en-emily,en-david\n"
                "```"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🎭 Voice Presets",
            value=(
                "• **alice**: Single female voice\n"
                "• **carter**: Single male voice\n"
                "• **conversation**: Balanced dialogue (alice + carter)\n"
                "• **debate**: Formal discussion (david + emily)\n"
                "• **podcast**: Multi-voice (alice + carter + david)\n"
                "• **news**: Professional (emily + carter)"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📝 Text Formatting",
            value=(
                "Auto-format: `\"Hello world!\"` → Single speaker\n"
                "Manual format: `\"Speaker1: Hi! Speaker2: Hello!\"` → Multi-speaker\n"
                "Natural dialogue: Voice assignments happen automatically"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⚡ Other Commands",
            value=(
                "`/voice_presets` - Show all available voices\n"
                "`/voice_status` - Check service status\n"
                "`/voice_help` - This help message"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🚀 Pro Tips",
            value=(
                "• Keep text under 2000 characters for best results\n"
                "• Use natural punctuation for better speech flow\n"
                "• Generation takes 30-60 seconds\n"
                "• Files are automatically cleaned up after 5 minutes"
            ),
            inline=False
        )
        
        embed.set_footer(text="Powered by Microsoft VibeVoice • Free & Open Source")
        
        await interaction.response.send_message(embed=embed)
    
    async def _cleanup_file(self, file_path: str, delay: int = 300):
        """Clean up generated audio file after delay."""
        try:
            await asyncio.sleep(delay)
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Cleaned up VibeVoice file: {file_path}")
        except Exception as e:
            logger.error(f"Error cleaning up file {file_path}: {e}")

# Standalone function to add VibeVoice commands to bot
async def setup_vibevoice_commands(bot: commands.Bot, cost_tracker: Optional[CostTracker] = None):
    """Add VibeVoice commands to the bot."""
    try:
        cog = VibeVoiceCommands(bot, cost_tracker)
        await bot.add_cog(cog)
        logger.info("VibeVoice commands added to bot")
        return cog
    except Exception as e:
        logger.error(f"Failed to add VibeVoice commands: {e}")
        return None