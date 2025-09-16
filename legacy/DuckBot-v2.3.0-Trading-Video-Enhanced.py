# -*- coding: utf-8 -*-
# ==============================================================================
# DUCK BOT v2.3.0 - TRADING VIDEO ENHANCED EDITION
# Features: Trading Video Integration, n8n ComfyUI Video Handling, All v2.2.7 features
# New: Auto-upload trading videos, video monitoring, crypto analysis commands
# ==============================================================================

# --- Windows UTF-8 Fix ---
import sys
import locale
if sys.platform == "win32":
    try:
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except:
        pass
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# --- 1. IMPORTS ---
import os
import json
import uuid
import urllib.request
import urllib.parse
from io import BytesIO
import traceback
from enum import Enum
import psutil
import gc

# Third-party libraries
import discord
import requests
import aiohttp
import websockets
import torch
import cv2
import tempfile
from PIL import Image
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

# Cost tracking imports
from duckbot.cost_tracker import CostTracker
from duckbot.cost_visualizer import CostVisualizer
from duckbot.cost_commands import CostCommands, setup_cost_commands

# VibeVoice TTS integration
try:
    from duckbot.vibevoice_commands import setup_vibevoice_commands
    VIBEVOICE_AVAILABLE = True
except ImportError:
    print("[WARN] VibeVoice not available - install with: python setup_vibevoice.py")
    VIBEVOICE_AVAILABLE = False
import datetime
import random
import hashlib
import re
import time
import asyncio
import websockets
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from neo4j import GraphDatabase
from collections import deque
from datetime import datetime, timedelta
from discord.ext import tasks
import speech_recognition as sr
import pyttsx3
import wave
import audioop
import threading
import queue as Queue
from io import BytesIO
import base64
import glob
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- 2. ENHANCED ERROR HANDLING CLASSES ---
class DuckBotError(Exception):
    """Base exception for DuckBot errors"""
    pass

class ComfyUIError(DuckBotError):
    """ComfyUI-related errors"""
    pass

class LMStudioError(DuckBotError):
    """LM Studio-related errors"""
    pass

class Neo4jError(DuckBotError):
    """Neo4j database-related errors"""
    pass

class QueueError(DuckBotError):
    """Queue management errors"""
    pass

class MemoryError(DuckBotError):
    """Memory management errors"""
    pass

# --- 3. PROGRESS TRACKING ---
class ProgressTracker:
    def __init__(self, total_steps: int, description: str = "Processing"):
        self.total_steps = total_steps
        self.current_step = 0
        self.description = description
        self.start_time = time.time()
        
    def update(self, step: int = None, description: str = None):
        if step is not None:
            self.current_step = step
        else:
            self.current_step += 1
        if description:
            self.description = description
            
    def get_progress_bar(self, width: int = 20) -> str:
        if self.total_steps == 0:
            return "█" * width
        filled = int((self.current_step / self.total_steps) * width)
        bar = "█" * filled + "░" * (width - filled)
        percentage = (self.current_step / self.total_steps) * 100
        elapsed = time.time() - self.start_time
        if self.current_step > 0:
            eta = (elapsed / self.current_step) * (self.total_steps - self.current_step)
            eta_str = f" ETA: {format_time(eta)}"
        else:
            eta_str = ""
        return f"`{bar}` {percentage:.1f}% {self.description}{eta_str}"

# --- 4. MEMORY MANAGEMENT ---
class MemoryManager:
    @staticmethod
    def get_memory_usage() -> dict:
        """Get current memory usage statistics"""
        memory = psutil.virtual_memory()
        return {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used
        }
    
    @staticmethod
    def check_memory_threshold(threshold_percent: float = 85.0) -> bool:
        """Check if memory usage is above threshold"""
        return psutil.virtual_memory().percent > threshold_percent
    
    @staticmethod
    def force_garbage_collection():
        """Force garbage collection to free memory"""
        gc.collect()
        torch.cuda.empty_cache() if torch.cuda.is_available() else None

# --- 5. INITIAL SETUP & CONFIGURATION ---
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# --- API URLs ---
LM_STUDIO_URL = "http://127.0.0.1:1234/v1/chat/completions"
LM_STUDIO_MODEL = os.getenv("LM_STUDIO_MODEL", "auto")
USE_LM_STUDIO_SYSTEM_PROMPT = os.getenv("USE_LM_STUDIO_SYSTEM_PROMPT", "true").lower() == "true"
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/duckbot-trading-news")

# Enhanced ComfyUI Configuration with Memory Management
COMFYUI_SERVERS = [
    {"address": "127.0.0.1:8188", "priority": 1, "max_concurrent": 2},
    {"address": "127.0.0.1:8189", "priority": 2, "max_concurrent": 1}
]
COMFYUI_SERVER_ADDRESS = "127.0.0.1:8188"  # Primary server for backward compatibility
MAX_MEMORY_THRESHOLD = float(os.getenv("MAX_MEMORY_THRESHOLD", "85.0"))
QUEUE_CLEANUP_INTERVAL = int(os.getenv("QUEUE_CLEANUP_INTERVAL", "300"))  # 5 minutes

# --- NEO4J DATABASE CONFIGURATION ---
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
# FIXED: Remove hardcoded password, require explicit environment variable
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_ENABLED = os.getenv("NEO4J_ENABLED", "false").lower() == "true"

# FIXED: Security check - disable Neo4j if password not properly configured
if NEO4J_ENABLED and not NEO4J_PASSWORD:
    print("WARNING: NEO4J_ENABLED=true but NEO4J_PASSWORD not set. Neo4j features disabled for security.")
    NEO4J_ENABLED = False

# Multi-server configuration
GLOBAL_ADMIN_IDS = [int(x) for x in os.getenv("GLOBAL_ADMIN_IDS", "").split(",") if x.strip()]
MAX_SERVERS_PER_INSTANCE = int(os.getenv("MAX_SERVERS_PER_INSTANCE", "100"))

# --- 6. ENHANCED QUEUE SYSTEM ---
@dataclass
class QueueItem:
    server_id: int
    user_id: int
    interaction: discord.Interaction
    prompt: str
    generation_type: str  # "image", "video", "batch"
    timestamp: float = field(default_factory=time.time)
    priority: int = 0  # Higher = more priority
    metadata: dict = field(default_factory=dict)
    progress_tracker: Optional[ProgressTracker] = None

@dataclass
class ComfyUIServer:
    address: str
    priority: int
    max_concurrent: int
    current_jobs: int = 0
    is_available: bool = True
    last_health_check: float = 0
    memory_usage: float = 0

class SmartQueueManager:
    def __init__(self):
        self.servers = [ComfyUIServer(**server) for server in COMFYUI_SERVERS]
        self.server_queues = {}
        self.image_history = {}  # server_id -> user_id -> [images]
        
    def get_best_server(self) -> Optional[ComfyUIServer]:
        """Get the best available server based on load and memory"""
        available_servers = [s for s in self.servers if s.is_available and s.current_jobs < s.max_concurrent]
        if not available_servers:
            return None
        # Sort by priority, then by current load
        return min(available_servers, key=lambda s: (s.priority, s.current_jobs))
    
    async def health_check_servers(self):
        """Check health of all ComfyUI servers"""
        for server in self.servers:
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                    async with session.get(f"http://{server.address}/system_stats") as response:
                        if response.status == 200:
                            stats = await response.json()
                            server.is_available = True
                            server.memory_usage = stats.get("memory_usage", 0)
                        else:
                            server.is_available = False
            except Exception:
                server.is_available = False
            server.last_health_check = time.time()

# Global instances
queue_manager = SmartQueueManager()
SERVER_QUEUES = {}
ASK_QUEUES = {}

# Global CLIENT_ID for ComfyUI
CLIENT_ID = str(uuid.uuid4())

def get_server_queue(server_id: int):
    """Get or create a server-specific queue."""
    if server_id not in SERVER_QUEUES:
        SERVER_QUEUES[server_id] = {
            'queue': deque(),
            'currently_processing': False,
            'lock': asyncio.Lock()
        }
    return SERVER_QUEUES[server_id]

def get_ask_queue(server_id: int):
    """Get or create a server-specific ask queue."""
    if server_id not in ASK_QUEUES:
        ASK_QUEUES[server_id] = {
            'queue': deque(),
            'currently_processing': False,
            'lock': asyncio.Lock()
        }
    return ASK_QUEUES[server_id]

# Average processing times for wait estimation
AVERAGE_TIMES = {
    "image": 15.0,
    "video": 45.0,
    "batch": 60.0
}

def update_average_time(generation_type: str, actual_time: float):
    """Update average processing time using exponential moving average."""
    alpha = 0.3
    AVERAGE_TIMES[generation_type] = (alpha * actual_time + 
                                    (1 - alpha) * AVERAGE_TIMES[generation_type])

def calculate_estimated_wait(position: int, generation_type: str) -> float:
    """Calculate estimated wait time based on queue position."""
    if position <= 1:
        return 0
    return (position - 1) * AVERAGE_TIMES[generation_type]

def format_time(seconds: float) -> str:
    """Format seconds into human-readable time."""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        return f"{minutes}m {remaining_seconds}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

# --- 7. ENHANCED COMFYUI FUNCTIONS ---
def queue_prompt(prompt_workflow, server_address: str = None):
    """Queue a prompt with enhanced error handling"""
    if server_address is None:
        server_address = COMFYUI_SERVER_ADDRESS
    
    try:
        p = {"prompt": prompt_workflow, "client_id": str(uuid.uuid4())}
        data = json.dumps(p).encode('utf-8')
        req = urllib.request.Request(f"http://{server_address}/prompt", data=data)
        response = urllib.request.urlopen(req, timeout=900)
        return json.loads(response.read())
    except urllib.error.HTTPError as e:
        raise ComfyUIError(f"HTTP {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        raise ComfyUIError(f"Connection failed: {e.reason}")
    except json.JSONDecodeError as e:
        raise ComfyUIError(f"Invalid JSON response: {e}")
    except Exception as e:
        raise ComfyUIError(f"Unexpected error: {e}")

def get_image(filename, subfolder, folder_type, server_address: str = None):
    """Get image with enhanced error handling"""
    if server_address is None:
        server_address = COMFYUI_SERVER_ADDRESS
        
    try:
        data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        url_values = urllib.parse.urlencode(data)
        with urllib.request.urlopen(f"http://{server_address}/view?{url_values}", timeout=900) as response:
            return response.read()
    except urllib.error.HTTPError as e:
        raise ComfyUIError(f"Image retrieval failed - HTTP {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        raise ComfyUIError(f"Image retrieval failed - Connection: {e.reason}")
    except Exception as e:
        raise ComfyUIError(f"Image retrieval failed: {e}")

def get_history(prompt_id, server_address: str = None):
    """Get history with enhanced error handling"""
    if server_address is None:
        server_address = COMFYUI_SERVER_ADDRESS
        
    try:
        with urllib.request.urlopen(f"http://{server_address}/history/{prompt_id}", timeout=900) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as e:
        raise ComfyUIError(f"History retrieval failed - HTTP {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        raise ComfyUIError(f"History retrieval failed - Connection: {e.reason}")
    except json.JSONDecodeError as e:
        raise ComfyUIError(f"Invalid history JSON: {e}")
    except Exception as e:
        raise ComfyUIError(f"History retrieval failed: {e}")

async def get_images_from_comfyui_with_progress(ws, prompt_workflow, progress_callback=None):
    """Enhanced image retrieval with progress tracking"""
    try:
        prompt_response = queue_prompt(prompt_workflow)
        if not prompt_response or 'prompt_id' not in prompt_response:
            raise ComfyUIError("Failed to queue prompt - no prompt_id returned")
            
        prompt_id = prompt_response['prompt_id']
        output_images = {}
        
        if progress_callback:
            await progress_callback("Workflow queued, processing...")
            
        while True:
            try:
                out = await asyncio.wait_for(ws.recv(), timeout=30.0)
                if isinstance(out, str):
                    message = json.loads(out)
                    
                    # Update progress based on message type
                    if progress_callback and message.get('type') == 'progress':
                        await progress_callback(f"Processing node {message.get('data', {}).get('node', 'unknown')}")
                    
                    if (message['type'] == 'executing' and 
                        message['data']['node'] is None and 
                        message['data']['prompt_id'] == prompt_id):
                        break
            except asyncio.TimeoutError:
                raise ComfyUIError("Timeout waiting for workflow completion")
            except websockets.exceptions.ConnectionClosed:
                raise ComfyUIError("WebSocket connection closed unexpectedly")
                
        if progress_callback:
            await progress_callback("Retrieving images...")
            
        history = get_history(prompt_id)[prompt_id]
        for node_id in history['outputs']:
            node_output = history['outputs'][node_id]
            if 'images' in node_output:
                images_output = []
                for img in node_output['images']:
                    try:
                        img_data = get_image(img['filename'], img['subfolder'], img['type'])
                        if img_data:
                            images_output.append(img_data)
                    except ComfyUIError as e:
                        print(f"Failed to retrieve image {img['filename']}: {e}")
                        continue
                output_images[node_id] = images_output
                
        if progress_callback:
            await progress_callback("Complete!")
            
        return output_images
        
    except Exception as e:
        if isinstance(e, ComfyUIError):
            raise
        raise ComfyUIError(f"Unexpected error in image generation: {e}")

async def run_comfyui_workflow_enhanced(workflow_data: dict, is_video: bool = False, progress_tracker: ProgressTracker = None) -> list:
    """Enhanced workflow execution with smart server selection and memory management"""
    
    # Check memory before starting
    if MemoryManager.check_memory_threshold(MAX_MEMORY_THRESHOLD):
        MemoryManager.force_garbage_collection()
        if MemoryManager.check_memory_threshold(MAX_MEMORY_THRESHOLD):
            raise MemoryError(f"Memory usage too high: {MemoryManager.get_memory_usage()['percent']:.1f}%")
    
    # Get best available server
    best_server = queue_manager.get_best_server()
    if not best_server:
        raise ComfyUIError("No ComfyUI servers available")
    
    server_address = best_server.address
    print(f"[TOOLS] Using ComfyUI server: {server_address}")
    
    try:
        best_server.current_jobs += 1
        
        if progress_tracker:
            progress_tracker.update(0, "Connecting to ComfyUI...")
            
        CLIENT_ID = str(uuid.uuid4())
        uri = f"ws://{server_address}/ws?clientId={CLIENT_ID}"
        
        async with websockets.connect(uri, ping_timeout=900, close_timeout=900) as ws:
            if progress_tracker:
                progress_tracker.update(1, "Connected, starting workflow...")
                
            images = await get_images_from_comfyui_with_progress(ws, workflow_data, progress_tracker)
            
            if not images:
                raise ComfyUIError("No images returned from ComfyUI")
            
            # Convert to expected format
            image_data_list = []
            for node_id in images:
                for img_data in images[node_id]:
                    if img_data:
                        image_data_list.append(img_data)
            
            # Store in image history
            return image_data_list
            
    except Exception as e:
        if isinstance(e, (ComfyUIError, MemoryError)):
            raise
        raise ComfyUIError(f"Workflow execution failed: {e}")
    finally:
        best_server.current_jobs = max(0, best_server.current_jobs - 1)
        MemoryManager.force_garbage_collection()

# --- 8. IMAGE HISTORY SYSTEM ---
class ImageHistoryManager:
    def __init__(self):
        self.user_histories = {}  # server_id -> user_id -> [image_records]
        self.max_history_per_user = 50
    
    def add_image(self, server_id: int, user_id: int, prompt: str, image_data: bytes, metadata: dict = None):
        """Add an image to user's history"""
        if server_id not in self.user_histories:
            self.user_histories[server_id] = {}
        if user_id not in self.user_histories[server_id]:
            self.user_histories[server_id][user_id] = []
        
        record = {
            'prompt': prompt,
            'timestamp': time.time(),
            'image_data': image_data,
            'metadata': metadata or {},
            'id': str(uuid.uuid4())
        }
        
        history = self.user_histories[server_id][user_id]
        history.append(record)
        
        # Maintain max history size
        if len(history) > self.max_history_per_user:
            history.pop(0)
    
    def get_user_history(self, server_id: int, user_id: int, limit: int = 10) -> list:
        """Get user's recent image history"""
        if server_id not in self.user_histories or user_id not in self.user_histories[server_id]:
            return []
        return self.user_histories[server_id][user_id][-limit:]
    
    def get_image_by_id(self, server_id: int, user_id: int, image_id: str) -> dict:
        """Get specific image by ID"""
        history = self.get_user_history(server_id, user_id, self.max_history_per_user)
        for record in history:
            if record['id'] == image_id:
                return record
        return None

# Global image history manager
image_history = ImageHistoryManager()

# --- 9. ENHANCED BOT INITIALIZATION ---
# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)
neo4j_driver = None

# Initialize cost tracker
cost_tracker = CostTracker()
cost_visualizer = CostVisualizer(cost_tracker)

# --- 10. NEO4J INITIALIZATION ---
def initialize_neo4j():
    """Initialize Neo4j connection and create database schema."""
    global neo4j_driver
    
    if not NEO4J_ENABLED:
        print("[WARN]  Neo4j disabled - enhanced features unavailable")
        return False
        
    try:
        neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        
        # Test connection and create initial schema
        with neo4j_driver.session() as session:
            # Create constraints and indexes for better performance
            schema_queries = [
                # Multi-server support - all nodes include server_id
                "CREATE CONSTRAINT IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (m:Message) REQUIRE (m.id, m.server_id) IS UNIQUE", 
                "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Channel) REQUIRE (c.id, c.server_id) IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Server) REQUIRE s.id IS UNIQUE",
                "CREATE INDEX IF NOT EXISTS FOR (m:Message) ON (m.server_id, m.timestamp)",
                "CREATE INDEX IF NOT EXISTS FOR (u:User) ON u.username",
                "CREATE INDEX IF NOT EXISTS FOR ()-[r:REACTS_TO]-() ON r.timestamp",
                
                # Enhanced schema for v2.2.4 features
                "CREATE CONSTRAINT IF NOT EXISTS FOR (k:Knowledge) REQUIRE (k.id, k.server_id) IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Concept) REQUIRE c.name IS UNIQUE",
                "CREATE INDEX IF NOT EXISTS FOR (k:Knowledge) ON (k.server_id, k.content)",
                "CREATE INDEX IF NOT EXISTS FOR (c:Concept) ON c.category",
                
                # Personal AI Memory (user-specific, not server-specific)
                "CREATE CONSTRAINT IF NOT EXISTS FOR (m:Memory) REQUIRE m.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Project) REQUIRE (p.id, p.user_id) IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (g:Goal) REQUIRE (g.id, g.user_id) IS UNIQUE",
                "CREATE INDEX IF NOT EXISTS FOR (m:Memory) ON (m.user_id, m.timestamp)",
                
                # Image and content tracking
                "CREATE CONSTRAINT IF NOT EXISTS FOR (art:Artwork) REQUIRE art.id IS UNIQUE",
                "CREATE INDEX IF NOT EXISTS FOR (art:Artwork) ON (art.user_id, art.created_date)",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (idea:Idea) REQUIRE idea.id IS UNIQUE",
                "CREATE INDEX IF NOT EXISTS FOR (idea:Idea) ON (idea.user_id, idea.tags)"
            ]
            
            for query in schema_queries:
                try:
                    session.run(query)
                except Exception as e:
                    print(f"Warning: Schema query failed: {e}")
                    
        print("[OK] Neo4j v2.2.7 database initialized successfully")
        return True
        
    except Exception as e:
        print(f"[FAIL] Failed to initialize Neo4j: {e}")
        return False

def close_neo4j():
    """Close Neo4j connection."""
    global neo4j_driver
    if neo4j_driver:
        neo4j_driver.close()
        neo4j_driver = None
        print("[OK] Neo4j connection closed")

# --- 11. ENHANCED COMFYUI WORKFLOW SYSTEM ---
async def run_comfyui_workflow(workflow_data: dict, is_video: bool = False, progress_callback=None) -> list:
    """Execute a ComfyUI workflow with enhanced error handling and progress tracking."""
    
    # Check memory before starting
    if MemoryManager.check_memory_threshold(MAX_MEMORY_THRESHOLD):
        MemoryManager.force_garbage_collection()
        if MemoryManager.check_memory_threshold(MAX_MEMORY_THRESHOLD):
            raise MemoryError(f"Memory usage too high: {MemoryManager.get_memory_usage()['percent']:.1f}%")
    
    # Get best available server
    best_server = queue_manager.get_best_server()
    if not best_server:
        # Fallback to primary server
        server_address = COMFYUI_SERVER_ADDRESS
        print(f"[WARN]  Using fallback server: {server_address}")
    else:
        server_address = best_server.address
        best_server.current_jobs += 1
        print(f"[TOOLS] Using ComfyUI server: {server_address}")
    
    try:
        CLIENT_ID = str(uuid.uuid4())
        uri = f"ws://{server_address}/ws?clientId={CLIENT_ID}"
        
        if progress_callback:
            await progress_callback("Connecting to ComfyUI...")
        
        async with websockets.connect(uri, ping_timeout=900, close_timeout=900) as ws:
            if progress_callback:
                await progress_callback("Connected, starting workflow...")
                
            images = await get_images_from_comfyui_with_progress(ws, workflow_data, progress_callback)
            
            if not images:
                raise ComfyUIError("No images returned from ComfyUI")
            
            # Convert to expected format
            image_data_list = []
            for node_id in images:
                for img_data in images[node_id]:
                    if img_data:
                        image_data_list.append(img_data)
            
            if progress_callback:
                await progress_callback(f"Complete! Generated {len(image_data_list)} images")
            
            return image_data_list
            
    except Exception as e:
        if isinstance(e, (ComfyUIError, MemoryError)):
            raise
        raise ComfyUIError(f"Workflow execution failed: {e}")
    finally:
        if best_server and hasattr(best_server, 'current_jobs'):
            best_server.current_jobs = max(0, best_server.current_jobs - 1)
        MemoryManager.force_garbage_collection()

# --- 12. ENHANCED BOT COMMANDS ---

@bot.event
async def on_ready():
    """
    Bot startup event - sync commands and initialize services
    """
    print(f'[SUCCESS] DuckBot v2.2.7 is online! Logged in as {bot.user}')
    print(f'[CHART] Connected to {len(bot.guilds)} servers')
    
    # Initialize Neo4j
    initialize_neo4j()
    
    # Health check external services (optional)
    try:
        await queue_manager.health_check_servers()
    except:
        pass  # ComfyUI removed - this is expected to fail
    
    # Setup cost tracking commands
    await setup_cost_commands(bot)
    
    # Initialize VibeVoice TTS
    if VIBEVOICE_AVAILABLE:
        try:
            await setup_vibevoice_commands(bot, cost_tracker)
            print("[EMOJI] VibeVoice TTS commands loaded")
        except Exception as e:
            print(f"[WARN] VibeVoice initialization failed: {e}")
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f'[OK] Synced {len(synced)} slash commands')
    except Exception as e:
        print(f'[FAIL] Failed to sync commands: {e}')

# --- 13. NEW QUEUE MANAGEMENT COMMANDS ---

@bot.tree.command(name="queue_status", description="Check your current position in the generation queue")
async def queue_status_command(interaction: discord.Interaction):
    """Check queue status for the current server"""
    try:
        await interaction.response.defer()
        
        server_queue = get_server_queue(interaction.guild.id)
        
        async with server_queue['lock']:
            queue_size = len(server_queue['queue'])
            currently_processing = server_queue['currently_processing']
        
        # Find user's position in queue
        user_position = None
        user_items = []
        
        async with server_queue['lock']:
            for i, item in enumerate(server_queue['queue']):
                if item.user_id == interaction.user.id:
                    if user_position is None:
                        user_position = i + 1
                    user_items.append({
                        'position': i + 1,
                        'prompt': item.prompt[:50] + '...' if len(item.prompt) > 50 else item.prompt,
                        'type': item.generation_type
                    })
        
        embed = discord.Embed(
            title="[CHART] Queue Status",
            color=0x3498db
        )
        
        embed.add_field(
            name="Server Queue",
            value=f"Total items: {queue_size}\nCurrently processing: {'Yes' if currently_processing else 'No'}",
            inline=True
        )
        
        if user_items:
            user_info = "\n".join([
                f"{item['position']}. {item['type'].title()}: {item['prompt']}"
                for item in user_items[:3]  # Show max 3 items
            ])
            if len(user_items) > 3:
                user_info += f"\n... and {len(user_items) - 3} more"
            
            embed.add_field(
                name="Your Items in Queue",
                value=user_info,
                inline=False
            )
            
            if user_position:
                wait_time = calculate_estimated_wait(user_position, user_items[0]['type'])
                embed.add_field(
                    name="Estimated Wait",
                    value=format_time(wait_time) if wait_time > 0 else "Processing now!",
                    inline=True
                )
        else:
            embed.add_field(
                name="Your Queue Status",
                value="No items in queue",
                inline=False
            )
        
        # Memory status
        memory_info = MemoryManager.get_memory_usage()
        embed.add_field(
            name="System Status",
            value=f"Memory: {memory_info['percent']:.1f}% used",
            inline=True
        )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await interaction.followup.send(f"[FAIL] Error checking queue status: {str(e)[:100]}")

@bot.tree.command(name="recent_images", description="View your recently generated images")
@app_commands.describe(limit="Number of recent images to show (1-10)")
async def recent_images_command(interaction: discord.Interaction, limit: int = 5):
    """Show user's recent image generation history"""
    try:
        await interaction.response.defer()
        
        limit = max(1, min(limit, 10))  # Clamp between 1 and 10
        
        history = image_history.get_user_history(interaction.guild.id, interaction.user.id, limit)
        
        if not history:
            await interaction.followup.send("[EMOJI] No image history found. Generate some images first!")
            return
        
        embed = discord.Embed(
            title=f"[ART] Your Recent Images ({len(history)} shown)",
            color=0xe74c3c
        )
        
        for i, record in enumerate(reversed(history[-limit:]), 1):
            timestamp = datetime.datetime.fromtimestamp(record['timestamp'])
            embed.add_field(
                name=f"{i}. {timestamp.strftime('%m/%d %H:%M')}",
                value=f"**Prompt:** {record['prompt'][:100]}{'...' if len(record['prompt']) > 100 else ''}\n**ID:** `{record['id'][:8]}...`",
                inline=False
            )
        
        embed.set_footer(text="Use /regenerate_image <id> to recreate an image")
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await interaction.followup.send(f"[FAIL] Error retrieving image history: {str(e)[:100]}")

@bot.tree.command(name="batch_generate", description="Generate multiple images with different seeds")
@app_commands.describe(
    prompt="Image prompt",
    count="Number of images to generate (1-4)",
    model="Model to use (auto/flux/sdxl/sd15)"
)
async def batch_generate_command(interaction: discord.Interaction, prompt: str, count: int = 2, model: str = "auto"):
    """Generate multiple images with different seeds"""
    try:
        await interaction.response.defer()
        
        count = max(1, min(count, 4))  # Limit to 4 images max
        
        # Check memory before batch operation
        if MemoryManager.check_memory_threshold(MAX_MEMORY_THRESHOLD - 10):  # Extra conservative for batch
            await interaction.followup.send("[WARN] System memory usage too high for batch generation. Please try again later.")
            return
        
        # Create progress tracker
        progress_tracker = ProgressTracker(count + 2, "Batch generation")
        
        # Create initial status message
        status_msg = await interaction.followup.send(
            embed=discord.Embed(
                title="[ART] Batch Image Generation",
                description=f"Generating {count} images...\n{progress_tracker.get_progress_bar()}",
                color=0x3498db
            )
        )
        
        async def update_progress(description: str):
            progress_tracker.update(description=description)
            try:
                embed = discord.Embed(
                    title="[ART] Batch Image Generation",
                    description=f"Generating {count} images...\n{progress_tracker.get_progress_bar()}",
                    color=0x3498db
                )
                await status_msg.edit(embed=embed)
            except Exception:
                pass  # Ignore edit failures
        
        # Load appropriate workflow
        workflow_files = {
            "flux": "workflow_flux_api.json",
            "sdxl": "workflow_sdxl_api.json", 
            "sd15": "workflow_api.json",
            "auto": "workflow_flux_api.json"  # Default to FLUX
        }
        
        workflow_file = workflow_files.get(model.lower(), "workflow_flux_api.json")
        
        try:
            with open(workflow_file, "r") as f:
                workflow_data = json.load(f)
        except FileNotFoundError:
            workflow_file = "workflow_api.json"  # Fallback
            with open(workflow_file, "r") as f:
                workflow_data = json.load(f)
        
        progress_tracker.update(1, "Workflow loaded")
        await update_progress("Workflow loaded")
        
        all_images = []
        
        for i in range(count):
            # Update prompt and generate new seed for each image
            workflow_data["3"]["inputs"]["text"] = prompt
            workflow_data["6"]["inputs"]["seed"] = torch.randint(1, 1125899906842624, (1,)).item()
            
            progress_tracker.update(description=f"Generating image {i+1}/{count}")
            await update_progress(f"Generating image {i+1}/{count}")
            
            try:
                images = await run_comfyui_workflow(workflow_data, progress_callback=update_progress)
                if images:
                    all_images.extend(images)
                    # Store in history
                    for img_data in images:
                        image_history.add_image(
                            interaction.guild.id,
                            interaction.user.id,
                            prompt,
                            img_data,
                            {'model': model, 'batch_index': i}
                        )
                        # Update user progression for each generated image
                        update_user_progress(interaction.user.id, interaction.guild.id, "generation")
            except Exception as e:
                print(f"Error generating image {i+1}: {e}")
                continue
        
        progress_tracker.update(progress_tracker.total_steps, "Complete!")
        await update_progress("Complete!")
        
        if all_images:
            # Create Discord files
            files = []
            for i, img_data in enumerate(all_images[:count]):
                files.append(discord.File(fp=BytesIO(img_data), filename=f"batch_{i+1}_{uuid.uuid4()}.png"))
            
            embed = discord.Embed(
                title="[OK] Batch Generation Complete!",
                description=f"Generated {len(files)} images\nPrompt: `{prompt}`\nModel: {model.upper()}",
                color=0x27ae60
            )
            
            await interaction.followup.send(embed=embed, files=files)
        else:
            await interaction.followup.send("[FAIL] Batch generation failed. No images were generated.")
            
    except Exception as e:
        await interaction.followup.send(f"[FAIL] Batch generation error: {str(e)[:100]}")

# --- 14. CORE IMAGE GENERATION COMMANDS ---

@bot.tree.command(name="ping", description="A simple command to test if the bot is responsive.")
async def ping_command(interaction: discord.Interaction):
    await interaction.response.send_message("Pong! [EMOJI] DuckBot v3.0.5 Professional WebUI Complete is running!", ephemeral=False)

@bot.tree.command(name="ask", description="Ask DuckBot a question directly - powered by LM Studio")
@app_commands.describe(question="Your question or prompt for DuckBot")
async def ask_command(interaction: discord.Interaction, question: str):
    """Direct LM Studio chat - no image/video generation"""
    try:
        await interaction.response.defer()
        
        # Send directly to LM Studio for chat
        lm_studio_url = "http://localhost:1234/v1/chat/completions"
        
        payload = {
            "model": "local-model",
            "messages": [
                {
                    "role": "system", 
                    "content": "You are DuckBot, a helpful AI assistant specializing in crypto trading and general knowledge. Keep responses concise and friendly."
                },
                {
                    "role": "user", 
                    "content": question
                }
            ],
            "temperature": 0.7,
            "max_tokens": 500,
            "stream": False
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(lm_studio_url, json=payload, timeout=30) as response:
                if response.status == 200:
                    result = await response.json()
                    answer = result.get('choices', [{}])[0].get('message', {}).get('content', 'No response received')
                    
                    # Track cost for local model (estimated tokens)
                    input_tokens = len(question.split()) * 1.3  # Rough token estimation
                    output_tokens = len(answer.split()) * 1.3
                    cost_tracker.track_usage(
                        provider="lmstudio",
                        model="local-model",
                        input_tokens=int(input_tokens),
                        output_tokens=int(output_tokens),
                        request_type="chat",
                        user_id=str(interaction.user.id)
                    )
                    
                    # Create response embed
                    embed = discord.Embed(
                        title="[EMOJI] DuckBot Response",
                        description=f"**Question:** {question}\n\n**Answer:** {answer}",
                        color=discord.Color.purple(),
                        timestamp=datetime.now()
                    )
                    
                    embed.set_footer(
                        text=f"Asked by {interaction.user.display_name} • Powered by LM Studio",
                        icon_url=interaction.user.display_avatar.url
                    )
                    
                    await interaction.followup.send(embed=embed)
                    
                else:
                    await interaction.followup.send(f"[FAIL] LM Studio error: {response.status}", ephemeral=True)
                    
    except asyncio.TimeoutError:
        await interaction.followup.send("[FAIL] Request timed out. LM Studio may be offline.", ephemeral=True)
    except Exception as e:
        logger.error(f"Error in ask command: {e}")
        await interaction.followup.send(f"[FAIL] Error: {str(e)}", ephemeral=True)

@bot.tree.command(name="voice_script", description="Generate a voice narration script with DuckBot branding")
@app_commands.describe(
    script="The script content to narrate",
    voice="Voice to use for generation"
)
@app_commands.choices(voice=[
    app_commands.Choice(name="Andrew (English US Male)", value="en-US-AndrewNeural"),
    app_commands.Choice(name="Sarah (English US Female)", value="en-US-SarahNeural"),
    app_commands.Choice(name="Brian (English UK Male)", value="en-GB-BrianNeural"),
    app_commands.Choice(name="Emma (English UK Female)", value="en-GB-EmmaNeural"),
])
async def voice_script_command(interaction: discord.Interaction, script: str, voice: str = "en-US-AndrewNeural"):
    """Generate voice narration with DuckBot branding"""
    try:
        await interaction.response.defer()
        
        # Add DuckBot branding prefix
        branded_script = f"*Brought to you by DuckBot* - {script}"
        
        # Send to n8n workflow for voice generation
        webhook_url = "http://localhost:5678/webhook/2e769c84-8b55-4dca-824b-347c073ce644"
        
        payload = {
            "prompt": branded_script,
            "voice": voice,
            "type": "voice_generation"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload, timeout=60) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Create response embed
                    embed = discord.Embed(
                        title="[EMOJI] Voice Generation Complete!",
                        description=f"**Script:** {script}\n**Voice:** {voice}\n**Branded Version:** {branded_script}",
                        color=discord.Color.blue(),
                        timestamp=datetime.now()
                    )
                    
                    embed.set_footer(
                        text=f"Generated by {interaction.user.display_name} • Powered by DuckBot",
                        icon_url=interaction.user.display_avatar.url
                    )
                    
                    await interaction.followup.send(embed=embed)
                    
                    # If audio file is returned, send it
                    if 'audio_url' in result:
                        await interaction.followup.send(result['audio_url'])
                    
                else:
                    await interaction.followup.send(f"[FAIL] Voice generation error: {response.status}", ephemeral=True)
                    
    except asyncio.TimeoutError:
        await interaction.followup.send("[FAIL] Voice generation timed out. Please try again.", ephemeral=True)
    except Exception as e:
        logger.error(f"Error in voice_script command: {e}")
        await interaction.followup.send(f"[FAIL] Error: {str(e)}", ephemeral=True)

# DISABLED: /generate command removed - replaced with voice generation
# @bot.tree.command(name="generate", description="Generate an image using ComfyUI with enhanced tracking.")
# @app_commands.describe(prompt="The prompt for the image.")
# async def generate_command(interaction: discord.Interaction, prompt: str):
#     try:
        await interaction.response.defer()
        
        # Check memory before generation
        if MemoryManager.check_memory_threshold(MAX_MEMORY_THRESHOLD):
            await interaction.followup.send("[WARN] System memory usage too high. Please try again later.")
            return
        
        # Create progress tracker
        progress_tracker = ProgressTracker(4, "Image generation")
        
        # Create status message
        status_embed = discord.Embed(
            title="[ART] Generating Image",
            description=f"Prompt: `{prompt}`\n{progress_tracker.get_progress_bar()}",
            color=0x3498db
        )
        status_msg = await interaction.followup.send(embed=status_embed)
        
        async def update_progress(description: str):
            progress_tracker.update(description=description)
            try:
                embed = discord.Embed(
                    title="[ART] Generating Image",
                    description=f"Prompt: `{prompt}`\n{progress_tracker.get_progress_bar()}",
                    color=0x3498db
                )
                await status_msg.edit(embed=embed)
            except Exception:
                pass
        
        # Load workflow
        try:
            with open("workflow_api.json", "r") as f:
                workflow_data = json.load(f)
        except FileNotFoundError:
            await interaction.followup.send("[FAIL] Error: workflow_api.json not found")
            return
        
        progress_tracker.update(1, "Workflow loaded")
        await update_progress("Workflow loaded")
        
        # Update prompt and generate seed
        workflow_data["3"]["inputs"]["text"] = prompt
        workflow_data["6"]["inputs"]["seed"] = torch.randint(1, 1125899906842624, (1,)).item()
        
        progress_tracker.update(2, "Starting generation...")
        await update_progress("Starting generation...")
        
        # Generate image
        images = await run_comfyui_workflow(workflow_data, progress_callback=update_progress)
        
        if not images:
            await status_msg.edit(embed=discord.Embed(
                title="[FAIL] Generation Failed",
                description=f"Prompt: `{prompt}`\nNo images were generated.",
                color=0xe74c3c
            ))
            return
        
        progress_tracker.update(4, "Complete!")
        await update_progress("Complete!")
        
        # Create Discord files and store in history
        files = []
        for i, img_data in enumerate(images):
            filename = f"generated_{uuid.uuid4()}.png"
            files.append(discord.File(fp=BytesIO(img_data), filename=filename))
            
            # Store in image history
            image_history.add_image(
                interaction.guild.id,
                interaction.user.id,
                prompt,
                img_data,
                {'model': 'sd15', 'command': 'generate'}
            )
        
        # Update user progression
        update_user_progress(interaction.user.id, interaction.guild.id, "generation")
        
        # Final success message
        success_embed = discord.Embed(
            title="[OK] Image Generation Complete!",
            description=f"Prompt: `{prompt}`\nGenerated {len(files)} image(s)",
            color=0x27ae60
        )
        
        await status_msg.edit(embed=success_embed)
        await interaction.followup.send(files=files)
        
    except ComfyUIError as e:
        await interaction.followup.send(f"[FAIL] ComfyUI Error: {str(e)[:100]}")
    except MemoryError as e:
        await interaction.followup.send(f"[FAIL] Memory Error: {str(e)[:100]}")
    except Exception as e:
        await interaction.followup.send(f"[FAIL] Generation error: {str(e)[:100]}")

# DISABLED: /animate and /generate commands removed - replaced with voice generation
# These functions have been replaced with /voice_script and /ask commands
def _removed_commands_placeholder():
    """Placeholder for removed /generate and /animate commands"""
    pass

# The /generate and /animate functions were here but have been removed
# for v3.0.5 to focus on voice generation and direct AI chat

# --- 16. FUN & ENGAGEMENT FEATURES ---

# Global storage for challenges, stories, and user progression
WEEKLY_CHALLENGES = {}
COLLABORATIVE_STORIES = {}
USER_PROGRESSION = {}
DISCOVERY_PROMPTS = [
    "A steampunk robot reading a book in a cozy library",
    "Floating islands connected by rainbow bridges in a cloudy sky",
    "A magical garden where flowers glow like stars at midnight",
    "An underwater city with bioluminescent architecture",
    "A forest where the trees are made of crystal and light",
    "A cosmic coffee shop floating between planets",
    "Ancient ruins covered in holographic vines",
    "A library where books fly around like birds",
    "A mountain made entirely of stacked vintage cameras",
    "A village built inside giant mushrooms with glowing windows",
    "Clockwork butterflies in a field of mechanical flowers",
    "A waterfall flowing upward into space filled with stars",
    "Dragons sleeping on clouds while aurora dances around them",
    "A train traveling through dimensions with windows showing different worlds",
    "A lighthouse that projects constellations instead of light",
    "Floating teacups with tiny worlds inside each one",
    "A desert where sand dunes are actually sleeping giants",
    "A city where buildings grow like trees and have leaves instead of roofs",
    "Whale songs visualized as colorful ribbons in the ocean",
    "A maze made of aurora borealis that changes with each step"
]

# Challenge themes for weekly challenges
CHALLENGE_THEMES = [
    {"theme": "Neon Dreams", "description": "Create something glowing and cyberpunk", "emoji": "[EMOJI]"},
    {"theme": "Nature's Magic", "description": "Combine natural elements with fantasy", "emoji": "[EMOJI]"},
    {"theme": "Retro Future", "description": "80s vision of the future", "emoji": "[EMOJI]"},
    {"theme": "Tiny Worlds", "description": "Miniature scenes with big impact", "emoji": "[EMOJI]"},
    {"theme": "Elemental Fusion", "description": "Combine fire, water, earth, and air", "emoji": "⚡"},
    {"theme": "Cosmic Journey", "description": "Space and celestial themes", "emoji": "[LAUNCH]"},
    {"theme": "Steampunk Wonder", "description": "Victorian-era meets advanced technology", "emoji": "[SETTINGS]"},
    {"theme": "Underwater Realm", "description": "Deep sea mysteries and beauty", "emoji": "[EMOJI]"},
    {"theme": "Time Paradox", "description": "Past, present, and future collide", "emoji": "⏰"},
    {"theme": "Gravity Defied", "description": "Things floating and flying impossibly", "emoji": "[EMOJI]"}
]

@dataclass
class Challenge:
    id: str
    theme: str
    description: str
    emoji: str
    start_date: datetime
    end_date: datetime
    server_id: int
    submissions: List[Dict] = field(default_factory=list)
    votes: Dict[str, List[int]] = field(default_factory=dict)  # submission_id -> [user_ids who voted]

@dataclass
class Story:
    id: str
    title: str
    server_id: int
    created_by: int
    created_at: datetime
    chapters: List[Dict] = field(default_factory=list)  # {"author": user_id, "text": str, "image": bytes, "timestamp": datetime}
    contributors: List[int] = field(default_factory=list)

@dataclass
class UserProgress:
    user_id: int
    server_id: int
    total_generations: int = 0
    challenges_completed: int = 0
    stories_contributed: int = 0
    discoveries_made: int = 0
    skill_level: str = "Novice"
    unlocked_features: List[str] = field(default_factory=list)
    badges: List[str] = field(default_factory=list)

def get_user_progress(user_id: int, server_id: int) -> UserProgress:
    """Get or create user progression data"""
    key = f"{server_id}_{user_id}"
    if key not in USER_PROGRESSION:
        USER_PROGRESSION[key] = UserProgress(user_id, server_id)
    return USER_PROGRESSION[key]

def update_user_progress(user_id: int, server_id: int, action: str):
    """Update user progression based on actions"""
    progress = get_user_progress(user_id, server_id)
    
    if action == "generation":
        progress.total_generations += 1
    elif action == "challenge":
        progress.challenges_completed += 1
    elif action == "story":
        progress.stories_contributed += 1
    elif action == "discovery":
        progress.discoveries_made += 1
    
    # Calculate skill level
    total_activity = (progress.total_generations + 
                     progress.challenges_completed * 5 + 
                     progress.stories_contributed * 3 + 
                     progress.discoveries_made * 2)
    
    if total_activity >= 100:
        progress.skill_level = "Master"
        if "priority_queue" not in progress.unlocked_features:
            progress.unlocked_features.append("priority_queue")
    elif total_activity >= 50:
        progress.skill_level = "Expert"
        if "batch_generation" not in progress.unlocked_features:
            progress.unlocked_features.append("batch_generation")
    elif total_activity >= 20:
        progress.skill_level = "Advanced"
        if "style_presets" not in progress.unlocked_features:
            progress.unlocked_features.append("style_presets")
    elif total_activity >= 5:
        progress.skill_level = "Intermediate"
    
    # Award badges
    if progress.total_generations >= 50 and "Generator" not in progress.badges:
        progress.badges.append("Generator")
    if progress.challenges_completed >= 5 and "Challenger" not in progress.badges:
        progress.badges.append("Challenger")
    if progress.stories_contributed >= 10 and "Storyteller" not in progress.badges:
        progress.badges.append("Storyteller")

# --- NEWS VIDEO GENERATION COMMAND ---

@bot.tree.command(name="generate_news_video", description="Generate professional news videos with Purple Sunshine news anchor overlay")
@app_commands.describe(
    prompt="The news content to generate", 
    news_type="Type of news: general, breaking, weather, sports, tech, finance"
)
@app_commands.choices(news_type=[
    app_commands.Choice(name="General News", value="general"),
    app_commands.Choice(name="Breaking News", value="breaking"),
    app_commands.Choice(name="Weather Report", value="weather"),
    app_commands.Choice(name="Sports News", value="sports"),
    app_commands.Choice(name="Tech News", value="tech"),
    app_commands.Choice(name="Financial News", value="finance")
])
async def generate_news_video_command(interaction: discord.Interaction, prompt: str, news_type: str = "general"):
    """Generate professional news videos with Purple Sunshine news anchor overlay using n8n + ComfyUI"""
    try:
        # Respond immediately to avoid timeout
        await interaction.response.send_message(
            f"[EMOJI] **News Video Generation Request**\n"
            f"**Type:** {news_type.title()} News\n"
            f"**Content:** `{prompt}`\n"
            f"[EMOJI] Connecting to enhanced n8n workflow...",
            ephemeral=False
        )
        
        # Prepare payload for n8n webhook
        payload = {
            "command": "generate_news_video",
            "prompt": prompt,
            "news_type": news_type,
            "user_id": str(interaction.user.id),
            "server_id": str(interaction.guild.id),
            "user_name": interaction.user.display_name
        }
        
        try:
            # Send request to n8n webhook
            response = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=300)  # 5 minute timeout
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    
                    if result.get('success', False):
                        # Create success embed
                        embed = discord.Embed(
                            title="[EMOJI] News Video Generated Successfully!",
                            description=f"**Content:** {prompt}\n**Type:** {news_type.title()} News\n[EMOJI] **News Anchor:** Purple Sunshine overlay applied",
                            color=0x00ff00
                        )
                        
                        # Add generation details
                        embed.add_field(name="[EMOJI] Seed", value=str(result.get('seed', 'N/A')), inline=True)
                        embed.add_field(name="⏱[EMOJI] Generation Time", value=f"{result.get('generation_time', 0):.1f}s", inline=True)
                        embed.add_field(name="[DIR] Files", value=str(result.get('total_files', 0)), inline=True)
                        
                        embed.set_footer(text="DuckBot v2.3.0 - Enhanced News Generator")
                        embed.timestamp = datetime.datetime.utcnow()
                        
                        # Send initial success message
                        await interaction.followup.send(embed=embed)
                        
                        # Now download and upload actual video/image files
                        files_uploaded = 0
                        upload_errors = []
                        
                        # Try to get files from ComfyUI directly
                        try:
                            # Get latest files from ComfyUI output directory
                            comfyui_history_url = f"http://127.0.0.1:8188/history"
                            history_response = requests.get(comfyui_history_url, timeout=30)
                            
                            if history_response.status_code == 200:
                                history_data = history_response.json()
                                
                                # Find the most recent generation (should be ours)
                                if history_data:
                                    latest_prompt_id = list(history_data.keys())[0]
                                    latest_generation = history_data[latest_prompt_id]
                                    
                                    if 'outputs' in latest_generation:
                                        outputs = latest_generation['outputs']
                                        
                                        # Process all outputs
                                        for node_id, node_output in outputs.items():
                                            
                                            # Handle images
                                            if 'images' in node_output:
                                                for img_info in node_output['images']:
                                                    try:
                                                        filename = img_info['filename']
                                                        subfolder = img_info.get('subfolder', '')
                                                        file_type = img_info.get('type', 'output')
                                                        
                                                        # Download image from ComfyUI
                                                        params = {
                                                            'filename': filename,
                                                            'subfolder': subfolder,
                                                            'type': file_type
                                                        }
                                                        
                                                        file_url = f"http://127.0.0.1:8188/view"
                                                        file_response = requests.get(file_url, params=params, timeout=60)
                                                        
                                                        if file_response.status_code == 200:
                                                            # Create Discord file
                                                            discord_file = discord.File(
                                                                BytesIO(file_response.content),
                                                                filename=filename
                                                            )
                                                            
                                                            # Upload to Discord
                                                            await interaction.followup.send(
                                                                f"[EMOJI][EMOJI] **{news_type.title()} News Image**\n*Generated with Purple Sunshine news anchor overlay*",
                                                                file=discord_file
                                                            )
                                                            files_uploaded += 1
                                                            
                                                        else:
                                                            upload_errors.append(f"Failed to download image {filename}")
                                                            
                                                    except Exception as img_error:
                                                        upload_errors.append(f"Image upload error: {str(img_error)}")
                                            
                                            # Handle videos/gifs
                                            if 'gifs' in node_output:
                                                for video_info in node_output['gifs']:
                                                    try:
                                                        filename = video_info['filename']
                                                        subfolder = video_info.get('subfolder', '')
                                                        file_type = video_info.get('type', 'output')
                                                        
                                                        # Download video from ComfyUI
                                                        params = {
                                                            'filename': filename,
                                                            'subfolder': subfolder,
                                                            'type': file_type
                                                        }
                                                        
                                                        file_url = f"http://127.0.0.1:8188/view"
                                                        file_response = requests.get(file_url, params=params, timeout=120)
                                                        
                                                        if file_response.status_code == 200:
                                                            # Create Discord file
                                                            discord_file = discord.File(
                                                                BytesIO(file_response.content),
                                                                filename=filename
                                                            )
                                                            
                                                            # Upload to Discord
                                                            await interaction.followup.send(
                                                                f"[EMOJI] **{news_type.title()} News Video**\n*Generated with Purple Sunshine news anchor overlay*",
                                                                file=discord_file
                                                            )
                                                            files_uploaded += 1
                                                            
                                                        else:
                                                            upload_errors.append(f"Failed to download video {filename}")
                                                            
                                                    except Exception as video_error:
                                                        upload_errors.append(f"Video upload error: {str(video_error)}")
                            
                        except Exception as comfyui_error:
                            upload_errors.append(f"ComfyUI connection error: {str(comfyui_error)}")
                        
                        # Send summary
                        if files_uploaded > 0:
                            await interaction.followup.send(
                                f"[OK] **Upload Complete!**\n"
                                f"Successfully uploaded {files_uploaded} file(s) to Discord!\n"
                                f"[EMOJI] All content includes Purple Sunshine news anchor overlay.",
                                ephemeral=True
                            )
                        else:
                            error_summary = "\n• ".join(upload_errors[:3])  # Show first 3 errors
                            await interaction.followup.send(
                                f"[WARN] **Files Generated But Upload Failed**\n"
                                f"Videos and images were created but couldn't be uploaded to Discord.\n"
                                f"**Errors:** {error_summary}\n"
                                f"Check ComfyUI output folder: `ComfyUI/output/NewsVideo_*`",
                                ephemeral=True
                            )
                    
                    else:
                        # Generation failed
                        error_msg = result.get('error', 'Unknown error occurred')
                        await interaction.followup.send(
                            f"[FAIL] **News Video Generation Failed**\n"
                            f"Error: {error_msg}\n"
                            f"Please check ComfyUI and n8n status."
                        )
                        
                except json.JSONDecodeError:
                    await interaction.followup.send(
                        f"[WARN] **Generation Completed**\n"
                        f"The news video was generated, but the response format was unexpected.\n"
                        f"Check ComfyUI output folder for your files."
                    )
                    
            else:
                await interaction.followup.send(
                    f"[FAIL] **Generation Failed**\n"
                    f"n8n webhook returned status {response.status_code}\n"
                    f"Please ensure:\n"
                    f"• n8n is running on localhost:5678\n"
                    f"• Enhanced workflow is imported\n"
                    f"• ComfyUI is running on 127.0.0.1:8188"
                )
                
        except requests.exceptions.Timeout:
            await interaction.followup.send(
                f"⏰ **Generation Timeout**\n"
                f"The news video generation took longer than 5 minutes.\n"
                f"This might be normal for complex generations.\n"
                f"Check ComfyUI output folder for results."
            )
            
        except requests.exceptions.ConnectionError:
            await interaction.followup.send(
                f"[EMOJI] **Connection Error**\n"
                f"Cannot connect to n8n webhook at: `{N8N_WEBHOOK_URL}`\n"
                f"Please ensure:\n"
                f"• n8n is running: `http://localhost:5678`\n"
                f"• Enhanced workflow is imported and active\n"
                f"• Webhook URL is correct in environment variables"
            )
            
        except Exception as e:
            await interaction.followup.send(
                f"[FAIL] **Unexpected Error**\n"
                f"Error: {str(e)}\n"
                f"Please check n8n and ComfyUI status."
            )
            
    except discord.NotFound:
        print(f"[WARN]  News video command interaction expired for user {interaction.user.name}")
    except Exception as e:
        print(f"[FAIL] Error in news video command: {e}")
        try:
            await interaction.followup.send(f"[FAIL] Command failed: {str(e)}", ephemeral=True)
        except:
            pass

# --- CHALLENGE SYSTEM COMMANDS ---

@bot.tree.command(name="challenge", description="View current weekly challenge or start a new one")
async def challenge_command(interaction: discord.Interaction):
    """View or manage weekly challenges"""
    try:
        await interaction.response.defer()
        
        server_id = interaction.guild.id
        current_challenge = None
        
        # Find current active challenge
        for challenge in WEEKLY_CHALLENGES.values():
            if (challenge.server_id == server_id and 
                challenge.start_date <= datetime.now() <= challenge.end_date):
                current_challenge = challenge
                break
        
        if current_challenge:
            # Show current challenge
            embed = discord.Embed(
                title=f"{current_challenge.emoji} Weekly Challenge: {current_challenge.theme}",
                description=current_challenge.description,
                color=0xf39c12
            )
            embed.add_field(
                name="⏰ Time Remaining",
                value=f"Ends {current_challenge.end_date.strftime('%Y-%m-%d %H:%M')}",
                inline=True
            )
            embed.add_field(
                name="[CHART] Submissions",
                value=f"{len(current_challenge.submissions)} entries",
                inline=True
            )
            embed.add_field(
                name="[TARGET] How to Participate",
                value="Use `/challenge_submit <prompt>` to enter!",
                inline=False
            )
            
            if current_challenge.submissions:
                recent_submissions = current_challenge.submissions[-3:]
                submission_text = "\\n".join([
                    f"• {sub['prompt'][:50]}..." if len(sub['prompt']) > 50 else f"• {sub['prompt']}"
                    for sub in recent_submissions
                ])
                embed.add_field(
                    name="[ART] Recent Submissions",
                    value=submission_text,
                    inline=False
                )
        else:
            # No active challenge, show option to start one
            embed = discord.Embed(
                title="[TARGET] No Active Challenge",
                description="No weekly challenge is currently running in this server.",
                color=0x95a5a6
            )
            embed.add_field(
                name="[LAUNCH] Start New Challenge",
                value="Use `/start_challenge` to begin a new weekly challenge!",
                inline=False
            )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await interaction.followup.send(f"[FAIL] Error viewing challenge: {str(e)[:100]}")

@bot.tree.command(name="start_challenge", description="Start a new weekly challenge (Admin only)")
async def start_challenge_command(interaction: discord.Interaction):
    """Start a new weekly challenge"""
    try:
        # Check if user has admin permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("[FAIL] Only administrators can start challenges!", ephemeral=True)
            return
            
        await interaction.response.defer()
        
        server_id = interaction.guild.id
        
        # Check if there's already an active challenge
        for challenge in WEEKLY_CHALLENGES.values():
            if (challenge.server_id == server_id and 
                challenge.start_date <= datetime.now() <= challenge.end_date):
                await interaction.followup.send("[FAIL] There's already an active challenge in this server!")
                return
        
        # Pick a random theme
        import random
        theme_data = random.choice(CHALLENGE_THEMES)
        
        # Create new challenge
        challenge_id = str(uuid.uuid4())
        start_date = datetime.now()
        end_date = start_date + timedelta(days=7)  # 1 week duration
        
        new_challenge = Challenge(
            id=challenge_id,
            theme=theme_data["theme"],
            description=theme_data["description"],
            emoji=theme_data["emoji"],
            start_date=start_date,
            end_date=end_date,
            server_id=server_id
        )
        
        WEEKLY_CHALLENGES[challenge_id] = new_challenge
        
        embed = discord.Embed(
            title=f"[SUCCESS] New Weekly Challenge Started!",
            description=f"{new_challenge.emoji} **{new_challenge.theme}**\\n{new_challenge.description}",
            color=0x27ae60
        )
        embed.add_field(
            name="⏰ Duration",
            value=f"Ends {end_date.strftime('%Y-%m-%d %H:%M')}",
            inline=True
        )
        embed.add_field(
            name="[TARGET] How to Participate",
            value="Use `/challenge_submit <prompt>` to enter!",
            inline=True
        )
        embed.add_field(
            name="[AWARD] Prizes",
            value="Winner gets priority queue access for a week!",
            inline=False
        )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await interaction.followup.send(f"[FAIL] Error starting challenge: {str(e)[:100]}")

@bot.tree.command(name="challenge_submit", description="Submit an entry to the current challenge")
@app_commands.describe(prompt="Your creative prompt for the challenge theme")
async def challenge_submit_command(interaction: discord.Interaction, prompt: str):
    """Submit entry to weekly challenge"""
    try:
        await interaction.response.defer()
        
        server_id = interaction.guild.id
        user_id = interaction.user.id
        
        # Find current active challenge
        current_challenge = None
        for challenge in WEEKLY_CHALLENGES.values():
            if (challenge.server_id == server_id and 
                challenge.start_date <= datetime.now() <= challenge.end_date):
                current_challenge = challenge
                break
        
        if not current_challenge:
            await interaction.followup.send("[FAIL] No active challenge in this server! Ask an admin to start one.")
            return
        
        # Check if user already submitted
        for submission in current_challenge.submissions:
            if submission["user_id"] == user_id:
                await interaction.followup.send("[FAIL] You've already submitted to this challenge!")
                return
        
        # Generate image for the challenge
        try:
            with open(r"C:\\Users\\Duck1\\Desktop\\workflow\\ComfyUI\\claude-enhanced-workflow.json", "r") as f:
                workflow_data = json.load(f)
        except FileNotFoundError:
            # Fallback to basic workflow
            with open("workflow_api.json", "r") as f:
                workflow_data = json.load(f)
        
        # Enhance prompt with challenge theme
        enhanced_prompt = f"{current_challenge.theme}: {prompt}"
        workflow_data["46"]["inputs"]["text"] = enhanced_prompt
        workflow_data["50"]["inputs"]["seed"] = torch.randint(1, 1125899906842624, (1,)).item()
        
        # Generate the image
        images = await run_comfyui_workflow(workflow_data)
        
        if images:
            # Store submission
            submission = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "username": interaction.user.display_name,
                "prompt": prompt,
                "enhanced_prompt": enhanced_prompt,
                "image_data": images[0],
                "timestamp": datetime.now(),
                "votes": 0
            }
            
            current_challenge.submissions.append(submission)
            current_challenge.votes[submission["id"]] = []
            
            # Update user progression
            update_user_progress(user_id, server_id, "challenge")
            
            # Create response
            embed = discord.Embed(
                title="[OK] Challenge Entry Submitted!",
                description=f"Your entry for **{current_challenge.theme}** has been submitted!",
                color=0x27ae60
            )
            embed.add_field(
                name="[ART] Your Prompt",
                value=prompt,
                inline=False
            )
            embed.add_field(
                name="[CHART] Total Entries",
                value=f"{len(current_challenge.submissions)} submissions",
                inline=True
            )
            
            # Send image
            file = discord.File(fp=BytesIO(images[0]), filename=f"challenge_{submission['id']}.png")
            await interaction.followup.send(embed=embed, file=file)
            
            # Store in image history
            image_history.add_image(
                server_id, user_id, enhanced_prompt, images[0],
                {'challenge_id': current_challenge.id, 'submission_id': submission["id"]}
            )
            
        else:
            await interaction.followup.send("[FAIL] Failed to generate image for challenge submission.")
        
    except Exception as e:
        await interaction.followup.send(f"[FAIL] Error submitting to challenge: {str(e)[:100]}")

@bot.tree.command(name="challenge_vote", description="Vote on challenge submissions")
async def challenge_vote_command(interaction: discord.Interaction):
    """Vote on challenge submissions"""
    try:
        await interaction.response.defer()
        
        server_id = interaction.guild.id
        user_id = interaction.user.id
        
        # Find current active challenge
        current_challenge = None
        for challenge in WEEKLY_CHALLENGES.values():
            if (challenge.server_id == server_id and 
                challenge.start_date <= datetime.now() <= challenge.end_date):
                current_challenge = challenge
                break
        
        if not current_challenge:
            await interaction.followup.send("[FAIL] No active challenge to vote on!")
            return
        
        if not current_challenge.submissions:
            await interaction.followup.send("[FAIL] No submissions to vote on yet!")
            return
        
        # Create voting embed with buttons
        embed = discord.Embed(
            title=f"[EMOJI][EMOJI] Vote for {current_challenge.theme} Challenge",
            description="React with [EMOJI] on submissions you like!",
            color=0x3498db
        )
        
        # Show recent submissions (limit to 5)
        for i, submission in enumerate(current_challenge.submissions[-5:], 1):
            vote_count = len(current_challenge.votes.get(submission["id"], []))
            embed.add_field(
                name=f"{i}. {submission['username']}",
                value=f"**Prompt:** {submission['prompt'][:100]}{'...' if len(submission['prompt']) > 100 else ''}\\n[EMOJI] {vote_count} votes",
                inline=False
            )
        
        embed.set_footer(text=f"Challenge ends {current_challenge.end_date.strftime('%Y-%m-%d %H:%M')}")
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await interaction.followup.send(f"[FAIL] Error showing challenge voting: {str(e)[:100]}")

# --- COLLABORATIVE STORYTELLING COMMANDS ---

@bot.tree.command(name="start_story", description="Start a new collaborative story")
@app_commands.describe(title="Title for your story", opening="Opening scene description")
async def start_story_command(interaction: discord.Interaction, title: str, opening: str):
    """Start a new collaborative story"""
    try:
        await interaction.response.defer()
        
        server_id = interaction.guild.id
        user_id = interaction.user.id
        
        # Generate opening image
        try:
            with open(r"C:\\Users\\Duck1\\Desktop\\workflow\\ComfyUI\\claude-enhanced-workflow.json", "r") as f:
                workflow_data = json.load(f)
        except FileNotFoundError:
            with open("workflow_api.json", "r") as f:
                workflow_data = json.load(f)
        
        # Create story-appropriate prompt
        story_prompt = f"Story illustration: {opening}, cinematic, detailed, book illustration style"
        workflow_data["46"]["inputs"]["text"] = story_prompt
        workflow_data["50"]["inputs"]["seed"] = torch.randint(1, 1125899906842624, (1,)).item()
        
        images = await run_comfyui_workflow(workflow_data)
        
        if images:
            # Create new story
            story_id = str(uuid.uuid4())
            story = Story(
                id=story_id,
                title=title,
                server_id=server_id,
                created_by=user_id,
                created_at=datetime.now()
            )
            
            # Add opening chapter
            opening_chapter = {
                "author": user_id,
                "author_name": interaction.user.display_name,
                "text": opening,
                "image": images[0],
                "timestamp": datetime.now()
            }
            story.chapters.append(opening_chapter)
            story.contributors.append(user_id)
            
            COLLABORATIVE_STORIES[story_id] = story
            
            # Update user progression
            update_user_progress(user_id, server_id, "story")
            
            embed = discord.Embed(
                title=f"[EMOJI] New Story Started: {title}",
                description=opening,
                color=0x9b59b6
            )
            embed.add_field(
                name="[EMOJI] Story ID",
                value=f"`{story_id[:8]}...`",
                inline=True
            )
            embed.add_field(
                name="[EMOJI] How to Continue",
                value="Use `/story_continue <story_id> <next_scene>`",
                inline=True
            )
            embed.set_footer(text=f"Started by {interaction.user.display_name}")
            
            file = discord.File(fp=BytesIO(images[0]), filename=f"story_{story_id}_ch1.png")
            await interaction.followup.send(embed=embed, file=file)
            
        else:
            await interaction.followup.send("[FAIL] Failed to generate opening image for story.")
        
    except Exception as e:
        await interaction.followup.send(f"[FAIL] Error starting story: {str(e)[:100]}")

@bot.tree.command(name="story_continue", description="Add the next chapter to a collaborative story")
@app_commands.describe(story_id="ID of the story to continue", next_scene="Description of what happens next")
async def story_continue_command(interaction: discord.Interaction, story_id: str, next_scene: str):
    """Continue a collaborative story"""
    try:
        await interaction.response.defer()
        
        server_id = interaction.guild.id
        user_id = interaction.user.id
        
        # Find the story
        story = None
        for s in COLLABORATIVE_STORIES.values():
            if s.server_id == server_id and s.id.startswith(story_id):
                story = s
                break
        
        if not story:
            await interaction.followup.send("[FAIL] Story not found! Use `/list_stories` to see available stories.")
            return
        
        # Generate image for new chapter
        try:
            with open(r"C:\\Users\\Duck1\\Desktop\\workflow\\ComfyUI\\claude-enhanced-workflow.json", "r") as f:
                workflow_data = json.load(f)
        except FileNotFoundError:
            with open("workflow_api.json", "r") as f:
                workflow_data = json.load(f)
        
        story_prompt = f"Story illustration: {next_scene}, continuing the story '{story.title}', cinematic, detailed, book illustration style"
        workflow_data["46"]["inputs"]["text"] = story_prompt
        workflow_data["50"]["inputs"]["seed"] = torch.randint(1, 1125899906842624, (1,)).item()
        
        images = await run_comfyui_workflow(workflow_data)
        
        if images:
            # Add new chapter
            chapter = {
                "author": user_id,
                "author_name": interaction.user.display_name,
                "text": next_scene,
                "image": images[0],
                "timestamp": datetime.now()
            }
            story.chapters.append(chapter)
            
            if user_id not in story.contributors:
                story.contributors.append(user_id)
            
            # Update user progression
            update_user_progress(user_id, server_id, "story")
            
            chapter_num = len(story.chapters)
            
            embed = discord.Embed(
                title=f"[EMOJI] {story.title} - Chapter {chapter_num}",
                description=next_scene,
                color=0x9b59b6
            )
            embed.add_field(
                name="[EMOJI][EMOJI] Author",
                value=interaction.user.display_name,
                inline=True
            )
            embed.add_field(
                name="[DOCS] Total Chapters",
                value=str(chapter_num),
                inline=True
            )
            embed.add_field(
                name="[EMOJI] Contributors",
                value=str(len(story.contributors)),
                inline=True
            )
            embed.set_footer(text=f"Story ID: {story.id[:8]}...")
            
            file = discord.File(fp=BytesIO(images[0]), filename=f"story_{story.id}_ch{chapter_num}.png")
            await interaction.followup.send(embed=embed, file=file)
            
        else:
            await interaction.followup.send("[FAIL] Failed to generate image for story chapter.")
        
    except Exception as e:
        await interaction.followup.send(f"[FAIL] Error continuing story: {str(e)[:100]}")

@bot.tree.command(name="list_stories", description="View active collaborative stories")
async def list_stories_command(interaction: discord.Interaction):
    """List all collaborative stories in the server"""
    try:
        await interaction.response.defer()
        
        server_id = interaction.guild.id
        
        server_stories = [s for s in COLLABORATIVE_STORIES.values() if s.server_id == server_id]
        
        if not server_stories:
            await interaction.followup.send("[EMOJI] No collaborative stories in this server yet! Use `/start_story` to begin one.")
            return
        
        embed = discord.Embed(
            title="[DOCS] Collaborative Stories",
            description=f"Found {len(server_stories)} stories in this server",
            color=0x9b59b6
        )
        
        for story in server_stories[-10:]:  # Show last 10 stories
            last_chapter = story.chapters[-1] if story.chapters else None
            embed.add_field(
                name=f"[EMOJI] {story.title}",
                value=f"**ID:** `{story.id[:8]}...`\\n**Chapters:** {len(story.chapters)}\\n**Contributors:** {len(story.contributors)}\\n**Last Update:** {last_chapter['timestamp'].strftime('%m/%d %H:%M') if last_chapter else 'Unknown'}",
                inline=True
            )
        
        embed.set_footer(text="Use /story_continue <id> <scene> to add to a story")
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await interaction.followup.send(f"[FAIL] Error listing stories: {str(e)[:100]}")

# --- RANDOM DISCOVERY MODE COMMANDS ---

@bot.tree.command(name="surprise_me", description="Generate a random creative image with surprise prompts")
async def surprise_me_command(interaction: discord.Interaction):
    """Random discovery mode - surprise generation"""
    try:
        await interaction.response.defer()
        
        server_id = interaction.guild.id
        user_id = interaction.user.id
        
        # Pick random discovery prompt
        import random
        surprise_prompt = random.choice(DISCOVERY_PROMPTS)
        
        # Add some random modifiers
        styles = ["photorealistic", "anime style", "oil painting", "digital art", "watercolor", "cyberpunk", "steampunk", "minimalist"]
        moods = ["dreamy", "vibrant", "mysterious", "peaceful", "epic", "whimsical", "dramatic", "serene"]
        
        style = random.choice(styles)
        mood = random.choice(moods)
        
        enhanced_prompt = f"{surprise_prompt}, {style}, {mood} atmosphere"
        
        # Generate the surprise image
        try:
            with open(r"C:\\Users\\Duck1\\Desktop\\workflow\\ComfyUI\\claude-enhanced-workflow.json", "r") as f:
                workflow_data = json.load(f)
        except FileNotFoundError:
            with open("workflow_api.json", "r") as f:
                workflow_data = json.load(f)
        
        workflow_data["46"]["inputs"]["text"] = enhanced_prompt
        workflow_data["50"]["inputs"]["seed"] = torch.randint(1, 1125899906842624, (1,)).item()
        
        images = await run_comfyui_workflow(workflow_data)
        
        if images:
            # Update user progression
            update_user_progress(user_id, server_id, "discovery")
            progress = get_user_progress(user_id, server_id)
            
            embed = discord.Embed(
                title="[EMOJI] Surprise Discovery!",
                description=f"**Random Prompt:** {surprise_prompt}",
                color=0xe67e22
            )
            embed.add_field(
                name="[ART] Style & Mood",
                value=f"{style.title()}, {mood}",
                inline=True
            )
            embed.add_field(
                name="[EMOJI] Discoveries Made",
                value=f"{progress.discoveries_made}",
                inline=True
            )
            embed.add_field(
                name="[EMOJI] Inspiration",
                value="Use `/surprise_me` again for more random creativity!",
                inline=False
            )
            
            file = discord.File(fp=BytesIO(images[0]), filename=f"surprise_{uuid.uuid4()}.png")
            await interaction.followup.send(embed=embed, file=file)
            
            # Store in image history
            image_history.add_image(
                server_id, user_id, enhanced_prompt, images[0],
                {'type': 'surprise', 'original_prompt': surprise_prompt}
            )
            
        else:
            await interaction.followup.send("[FAIL] Failed to generate surprise image. Try again!")
        
    except Exception as e:
        await interaction.followup.send(f"[FAIL] Error generating surprise: {str(e)[:100]}")

@bot.tree.command(name="inspire_me", description="Get random creative prompts for inspiration")
async def inspire_me_command(interaction: discord.Interaction):
    """Get random creative inspiration"""
    try:
        import random
        
        # Generate 3 random inspirations
        selected_prompts = random.sample(DISCOVERY_PROMPTS, 3)
        
        embed = discord.Embed(
            title="[EMOJI] Creative Inspiration",
            description="Here are some random creative prompts to spark your imagination!",
            color=0xf39c12
        )
        
        for i, prompt in enumerate(selected_prompts, 1):
            embed.add_field(
                name=f"[EMOJI] Inspiration {i}",
                value=prompt,
                inline=False
            )
        
        embed.add_field(
            name="[ART] How to Use",
            value="Copy a prompt you like and use it with `/generate` or modify it to your taste!",
            inline=False
        )
        embed.set_footer(text="Use /surprise_me to generate images from random prompts automatically!")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        await interaction.response.send_message(f"[FAIL] Error getting inspiration: {str(e)[:100]}", ephemeral=True)

# --- SKILL PROGRESSION SYSTEM COMMANDS ---

@bot.tree.command(name="my_progress", description="View your skill progression and unlocked features")
async def my_progress_command(interaction: discord.Interaction):
    """View user skill progression"""
    try:
        server_id = interaction.guild.id
        user_id = interaction.user.id
        
        progress = get_user_progress(user_id, server_id)
        
        embed = discord.Embed(
            title=f"[CHART] {interaction.user.display_name}'s Progress",
            description=f"Skill Level: **{progress.skill_level}**",
            color=0x3498db
        )
        
        # Activity stats
        embed.add_field(
            name="[ART] Activity Stats",
            value=f"Images Generated: {progress.total_generations}\\nChallenges Completed: {progress.challenges_completed}\\nStory Contributions: {progress.stories_contributed}\\nDiscoveries Made: {progress.discoveries_made}",
            inline=True
        )
        
        # Skill progression
        total_activity = (progress.total_generations + 
                         progress.challenges_completed * 5 + 
                         progress.stories_contributed * 3 + 
                         progress.discoveries_made * 2)
        
        next_level_req = 0
        if progress.skill_level == "Novice":
            next_level_req = 5 - total_activity
            next_level = "Intermediate"
        elif progress.skill_level == "Intermediate":
            next_level_req = 20 - total_activity
            next_level = "Advanced"
        elif progress.skill_level == "Advanced":
            next_level_req = 50 - total_activity
            next_level = "Expert"
        elif progress.skill_level == "Expert":
            next_level_req = 100 - total_activity
            next_level = "Master"
        else:
            next_level = "Master (Max Level)"
            next_level_req = 0
        
        if next_level_req > 0:
            embed.add_field(
                name="⬆[EMOJI] Next Level",
                value=f"To {next_level}: {next_level_req} more activity points",
                inline=True
            )
        else:
            embed.add_field(
                name="[AWARD] Status",
                value="Maximum level reached!",
                inline=True
            )
        
        # Unlocked features
        if progress.unlocked_features:
            features_text = "\\n".join([f"[OK] {feature.replace('_', ' ').title()}" for feature in progress.unlocked_features])
            embed.add_field(
                name="[EMOJI] Unlocked Features",
                value=features_text,
                inline=False
            )
        
        # Badges
        if progress.badges:
            badges_text = "\\n".join([f"[EMOJI] {badge}" for badge in progress.badges])
            embed.add_field(
                name="[AWARD] Badges Earned",
                value=badges_text,
                inline=False
            )
        
        # Progress bar
        progress_bar_length = 20
        if progress.skill_level == "Master":
            filled = progress_bar_length
        else:
            level_caps = {"Novice": 5, "Intermediate": 20, "Advanced": 50, "Expert": 100}
            current_cap = level_caps.get(progress.skill_level, 100)
            filled = min(progress_bar_length, int((total_activity / current_cap) * progress_bar_length))
        
        progress_bar = "█" * filled + "░" * (progress_bar_length - filled)
        embed.add_field(
            name="[EMOJI] Progress",
            value=f"`{progress_bar}` {total_activity} activity points",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        await interaction.response.send_message(f"[FAIL] Error viewing progress: {str(e)[:100]}", ephemeral=True)

@bot.tree.command(name="leaderboard", description="View the server's skill progression leaderboard")
async def leaderboard_command(interaction: discord.Interaction):
    """View server leaderboard"""
    try:
        await interaction.response.defer()
        
        server_id = interaction.guild.id
        
        # Get all users for this server
        server_users = []
        for key, progress in USER_PROGRESSION.items():
            if progress.server_id == server_id:
                total_activity = (progress.total_generations + 
                                progress.challenges_completed * 5 + 
                                progress.stories_contributed * 3 + 
                                progress.discoveries_made * 2)
                server_users.append((progress, total_activity))
        
        if not server_users:
            await interaction.followup.send("[CHART] No activity data yet! Start generating to appear on the leaderboard.")
            return
        
        # Sort by activity level
        server_users.sort(key=lambda x: x[1], reverse=True)
        
        embed = discord.Embed(
            title="[AWARD] Server Leaderboard",
            description="Top contributors in this server",
            color=0xf1c40f
        )
        
        for i, (progress, activity) in enumerate(server_users[:10], 1):
            try:
                user = bot.get_user(progress.user_id)
                username = user.display_name if user else f"User {progress.user_id}"
            except:
                username = f"User {progress.user_id}"
            
            medal = "[EMOJI]" if i == 1 else "[EMOJI]" if i == 2 else "[EMOJI]" if i == 3 else f"{i}."
            
            embed.add_field(
                name=f"{medal} {username}",
                value=f"**{progress.skill_level}** ({activity} points)\\nGenerations: {progress.total_generations} | Challenges: {progress.challenges_completed}",
                inline=False
            )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await interaction.followup.send(f"[FAIL] Error showing leaderboard: {str(e)[:100]}")

# Hook into existing generation commands to update progression
def update_generation_progress(user_id: int, server_id: int):
    """Call this after successful image generation"""
    update_user_progress(user_id, server_id, "generation")

# --- 17. TRADING VIDEO SYSTEM ---

# Trading video monitoring configuration
TRADING_VIDEO_PATH = os.path.join(os.path.dirname(__file__), "ComfyUI_windows_portable_nvidia", "ComfyUI_windows_portable", "ComfyUI", "output")
TRADING_CHANNEL_ID = int(os.getenv('TRADING_CHANNEL_ID', '1282464171088302182'))  # Default to crypto-alerts
TRADING_VIDEO_EXTENSIONS = ['.mp4', '.mov', '.avi', '.mkv']
VIDEO_SIZE_LIMIT = 25 * 1024 * 1024  # 25MB Discord limit

# ComfyUI trading workflow path
TRADING_WORKFLOW_PATH = r"C:\Users\Duck1\Desktop\workflow\ComfyUI\trading-news-video-workflow.json"

# Global video monitoring state
video_monitor_active = False
video_observer = None
processed_videos = set()

class TradingVideoHandler(FileSystemEventHandler):
    """Handles new trading video files from ComfyUI"""
    
    def __init__(self, bot):
        self.bot = bot
    
    def on_created(self, event):
        if event.is_dir:
            return
            
        file_path = event.src_path
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Check if it's a video file and contains trading keywords
        if (file_ext in TRADING_VIDEO_EXTENSIONS and 
            ('Trading_News_Report' in file_path or 'trading' in file_path.lower())):
            
            # Avoid duplicate processing
            if file_path in processed_videos:
                return
            processed_videos.add(file_path)
            
            print(f"[EMOJI] New trading video detected: {file_path}")
            
            # Schedule upload with delay to ensure file is fully written
            asyncio.create_task(self.upload_trading_video_delayed(file_path))
    
    async def upload_trading_video_delayed(self, file_path):
        """Upload trading video with delay to ensure completion"""
        try:
            # Wait for file to be fully written
            await asyncio.sleep(2)
            
            # Verify file exists and has reasonable size
            if not os.path.exists(file_path):
                print(f"[FAIL] Trading video file not found: {file_path}")
                return
            
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                print(f"[FAIL] Trading video file is empty: {file_path}")
                return
            
            if file_size > VIDEO_SIZE_LIMIT:
                print(f"[WARN] Trading video too large ({file_size} bytes): {file_path}")
                return
            
            # Get the trading channel
            channel = self.bot.get_channel(TRADING_CHANNEL_ID)
            if not channel:
                print(f"[FAIL] Trading channel not found: {TRADING_CHANNEL_ID}")
                return
            
            # Extract video filename
            filename = os.path.basename(file_path)
            
            # Create embed for trading video
            embed = discord.Embed(
                title="[EMOJI] Trading News Video Report",
                description="Your automated crypto analysis video has been generated!",
                color=0x00ff88,
                timestamp=datetime.utcnow()
            )
            embed.add_field(
                name="[CHART] Analysis Features", 
                value="• Professional newsroom setting\n• AI-powered narration\n• Real-time market data\n• Expert trading insights", 
                inline=False
            )
            embed.add_field(
                name="[EMOJI] Video Details",
                value=f"• **Filename:** `{filename}`\n• **Size:** `{file_size // 1024:.1f} KB`\n• **Format:** Professional MP4",
                inline=False
            )
            embed.set_footer(text="Generated by DuckBot v2.3.0 | ComfyUI + n8n Integration")
            
            # Upload video file
            with open(file_path, 'rb') as video_file:
                discord_file = discord.File(video_file, filename=filename)
                await channel.send(embed=embed, file=discord_file)
            
            print(f"[OK] Trading video uploaded successfully: {filename}")
            
        except Exception as e:
            print(f"[FAIL] Error uploading trading video: {e}")
            traceback.print_exc()

@app_commands.describe(
    action="Start or stop trading video monitoring"
)
async def trading_monitor_command(interaction: discord.Interaction, action: str):
    """Start or stop monitoring for new trading videos"""
    global video_monitor_active, video_observer
    
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("[FAIL] Administrator permissions required", ephemeral=True)
        return
    
    action = action.lower()
    
    if action == "start":
        if video_monitor_active:
            await interaction.response.send_message("[OK] Trading video monitoring is already active", ephemeral=True)
            return
        
        try:
            # Ensure the video path exists
            if not os.path.exists(TRADING_VIDEO_PATH):
                await interaction.response.send_message(f"[FAIL] Trading video path not found: `{TRADING_VIDEO_PATH}`", ephemeral=True)
                return
            
            # Create and start file observer
            video_observer = Observer()
            event_handler = TradingVideoHandler(bot)
            video_observer.schedule(event_handler, TRADING_VIDEO_PATH, recursive=False)
            video_observer.start()
            
            video_monitor_active = True
            
            embed = discord.Embed(
                title="[EMOJI] Trading Video Monitor Started",
                description="Now monitoring for new trading videos from ComfyUI",
                color=0x00ff00
            )
            embed.add_field(name="[DIR] Watch Path", value=f"`{TRADING_VIDEO_PATH}`", inline=False)
            embed.add_field(name="[EMOJI] Upload Channel", value=f"<#{TRADING_CHANNEL_ID}>", inline=False)
            embed.add_field(name="[TARGET] File Types", value="`.mp4`, `.mov`, `.avi`, `.mkv`", inline=False)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            print(f"[EMOJI] Trading video monitoring started: {TRADING_VIDEO_PATH}")
            
        except Exception as e:
            await interaction.response.send_message(f"[FAIL] Error starting video monitor: {e}", ephemeral=True)
            print(f"[FAIL] Video monitor error: {e}")
    
    elif action == "stop":
        if not video_monitor_active:
            await interaction.response.send_message("[WARN] Trading video monitoring is not active", ephemeral=True)
            return
        
        try:
            if video_observer:
                video_observer.stop()
                video_observer.join()
                video_observer = None
            
            video_monitor_active = False
            
            embed = discord.Embed(
                title="[STOP] Trading Video Monitor Stopped",
                description="Trading video monitoring has been disabled",
                color=0xff6600
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            print("[STOP] Trading video monitoring stopped")
            
        except Exception as e:
            await interaction.response.send_message(f"[FAIL] Error stopping video monitor: {e}", ephemeral=True)
            print(f"[FAIL] Video monitor stop error: {e}")
    
    else:
        await interaction.response.send_message("[FAIL] Invalid action. Use `start` or `stop`", ephemeral=True)

@app_commands.describe()
async def trading_status_command(interaction: discord.Interaction):
    """Check trading video monitoring status"""
    
    embed = discord.Embed(
        title="[CHART] Trading Video System Status",
        color=0x0099ff,
        timestamp=datetime.utcnow()
    )
    
    # Monitor status
    status_emoji = "[EMOJI]" if video_monitor_active else "[EMOJI]"
    status_text = "Active" if video_monitor_active else "Inactive"
    embed.add_field(name="[EMOJI] Video Monitor", value=f"{status_emoji} {status_text}", inline=True)
    
    # Path status
    path_exists = os.path.exists(TRADING_VIDEO_PATH)
    path_emoji = "[OK]" if path_exists else "[FAIL]"
    embed.add_field(name="[DIR] Watch Path", value=f"{path_emoji} Path exists", inline=True)
    
    # Channel status
    channel = bot.get_channel(TRADING_CHANNEL_ID)
    channel_emoji = "[OK]" if channel else "[FAIL]"
    channel_text = f"<#{TRADING_CHANNEL_ID}>" if channel else "Not found"
    embed.add_field(name="[EMOJI] Upload Channel", value=f"{channel_emoji} {channel_text}", inline=True)
    
    # Video count
    if path_exists:
        video_files = []
        for ext in TRADING_VIDEO_EXTENSIONS:
            video_files.extend(glob.glob(os.path.join(TRADING_VIDEO_PATH, f"*{ext}")))
        embed.add_field(name="[EMOJI] Videos in Path", value=f"{len(video_files)} files", inline=True)
    
    # Processed count
    embed.add_field(name="[EMOJI] Processed Videos", value=f"{len(processed_videos)} uploaded", inline=True)
    
    # Configuration
    embed.add_field(name="[SETTINGS] Settings", value=f"Max size: {VIDEO_SIZE_LIMIT // (1024*1024)}MB", inline=True)
    
    embed.add_field(
        name="[FOLDER] Full Path", 
        value=f"`{TRADING_VIDEO_PATH}`", 
        inline=False
    )
    
    await interaction.response.send_message(embed=embed)

@app_commands.describe(
    filename="Name of the video file to upload manually"
)
async def trading_upload_command(interaction: discord.Interaction, filename: str):
    """Manually upload a specific trading video"""
    
    await interaction.response.defer()
    
    try:
        # Build full file path
        file_path = os.path.join(TRADING_VIDEO_PATH, filename)
        
        # Check if file exists
        if not os.path.exists(file_path):
            await interaction.followup.send(f"[FAIL] Video file not found: `{filename}`")
            return
        
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > VIDEO_SIZE_LIMIT:
            await interaction.followup.send(f"[FAIL] Video too large ({file_size // (1024*1024)}MB). Discord limit is 25MB.")
            return
        
        # Upload video
        embed = discord.Embed(
            title="[EMOJI] Manual Trading Video Upload",
            description=f"Uploading video: `{filename}`",
            color=0x00ff88,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="[DIR] File Size", value=f"{file_size // 1024:.1f} KB", inline=True)
        embed.add_field(name="[EMOJI] Uploaded by", value=interaction.user.mention, inline=True)
        
        with open(file_path, 'rb') as video_file:
            discord_file = discord.File(video_file, filename=filename)
            await interaction.followup.send(embed=embed, file=discord_file)
        
        print(f"[OK] Manual trading video upload: {filename} by {interaction.user}")
        
    except Exception as e:
        await interaction.followup.send(f"[FAIL] Error uploading video: {e}")
        print(f"[FAIL] Manual upload error: {e}")

@app_commands.describe()
async def trading_list_command(interaction: discord.Interaction):
    """List available trading videos"""
    
    try:
        if not os.path.exists(TRADING_VIDEO_PATH):
            await interaction.response.send_message(f"[FAIL] Trading video path not found: `{TRADING_VIDEO_PATH}`")
            return
        
        # Find all video files
        video_files = []
        for ext in TRADING_VIDEO_EXTENSIONS:
            pattern = os.path.join(TRADING_VIDEO_PATH, f"*{ext}")
            video_files.extend(glob.glob(pattern))
        
        if not video_files:
            await interaction.response.send_message("[DIR] No trading videos found in the output directory")
            return
        
        # Sort by modification time (newest first)
        video_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        # Create embed
        embed = discord.Embed(
            title="[DIR] Available Trading Videos",
            description=f"Found {len(video_files)} video files",
            color=0x0099ff
        )
        
        # Show up to 10 most recent videos
        for i, file_path in enumerate(video_files[:10]):
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            
            size_mb = file_size / (1024 * 1024)
            size_text = f"{size_mb:.1f}MB" if size_mb >= 1 else f"{file_size // 1024}KB"
            
            embed.add_field(
                name=f"[EMOJI] {filename}",
                value=f"Size: {size_text} | Modified: {mod_time.strftime('%m/%d %H:%M')}",
                inline=False
            )
        
        if len(video_files) > 10:
            embed.add_field(
                name="[FOLDER] More Files",
                value=f"... and {len(video_files) - 10} more videos",
                inline=False
            )
        
        embed.set_footer(text=f"Path: {TRADING_VIDEO_PATH}")
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        await interaction.response.send_message(f"[FAIL] Error listing videos: {e}")
        print(f"[FAIL] Video list error: {e}")

async def generate_trading_video(analysis_text: str, channel_id: int = None) -> bool:
    """Generate trading video from analysis text using ComfyUI"""
    try:
        # Load trading workflow
        with open(TRADING_WORKFLOW_PATH, "r") as f:
            workflow_data = json.load(f)
        
        # Update TTS script with trading analysis
        # Look for node 102 in the workflow structure
        nodes_found = False
        if "nodes" in workflow_data:
            # Handle UI workflow format (with nodes array)
            for node in workflow_data["nodes"]:
                if node["id"] == 102 and node["type"] == "String":
                    node["widgets_values"][0] = analysis_text
                    nodes_found = True
                    break
        elif "102" in workflow_data:
            # Handle API workflow format (direct node access)
            workflow_data["102"]["inputs"]["value"] = analysis_text
            nodes_found = True
            
        if not nodes_found:
            print("[FAIL] Warning: TTS Script node (102) not found in workflow")
            return False
        
        # Update seeds for uniqueness
        import random
        seed = random.randint(1, 1125899906842624)
        if "50" in workflow_data:  # Video KSampler
            workflow_data["50"]["inputs"]["seed"] = seed
        if "3" in workflow_data:   # Audio KSampler
            workflow_data["3"]["inputs"]["seed"] = seed
        
        print(f"[EMOJI] Generating trading video with analysis: {analysis_text[:100]}...")
        
        # Execute ComfyUI workflow
        video_data_list = await run_comfyui_workflow(workflow_data, is_video=True)
        
        if video_data_list:
            print("[OK] Trading video generated successfully!")
            return True
        else:
            print("[FAIL] No video data returned from ComfyUI")
            return False
            
    except Exception as e:
        print(f"[FAIL] Error generating trading video: {e}")
        return False

@app_commands.describe(
    analysis_text="Trading analysis text to convert into video narration"
)
async def generate_trading_news_command(interaction: discord.Interaction, analysis_text: str):
    """Generate a trading news video from analysis text"""
    
    await interaction.response.defer()
    
    try:
        if len(analysis_text) < 50:
            await interaction.followup.send("[FAIL] Analysis text too short. Please provide at least 50 characters.")
            return
        
        if len(analysis_text) > 2000:
            await interaction.followup.send("[FAIL] Analysis text too long. Please keep under 2000 characters.")
            return
        
        # Create progress embed
        embed = discord.Embed(
            title="[EMOJI] Generating Trading News Video",
            description="Creating professional news report with TTS narration...",
            color=0xffaa00
        )
        embed.add_field(name="[EMOJI] Analysis Preview", value=f"`{analysis_text[:200]}{'...' if len(analysis_text) > 200 else ''}`", inline=False)
        embed.add_field(name="⏱[EMOJI] Status", value="[EMOJI] Initializing ComfyUI workflow...", inline=False)
        embed.set_footer(text="This may take 30-60 seconds")
        
        status_msg = await interaction.followup.send(embed=embed)
        
        # Generate video
        success = await generate_trading_video(analysis_text, interaction.channel_id)
        
        if success:
            success_embed = discord.Embed(
                title="[OK] Trading News Video Generated!",
                description="Video has been created and should appear shortly via auto-monitoring.",
                color=0x00ff00
            )
            success_embed.add_field(name="[DIR] Output Location", value=f"`{TRADING_VIDEO_PATH}`", inline=False)
            success_embed.add_field(name="[EMOJI] Monitor Status", value="Video will be auto-uploaded when detected", inline=False)
            await status_msg.edit(embed=success_embed)
        else:
            error_embed = discord.Embed(
                title="[FAIL] Video Generation Failed",
                description="There was an error creating the trading video. Check ComfyUI status.",
                color=0xff0000
            )
            await status_msg.edit(embed=error_embed)
            
    except Exception as e:
        await interaction.followup.send(f"[FAIL] Error: {e}")
        print(f"[FAIL] Trading video generation error: {e}")

# Add trading commands to the bot
bot.tree.add_command(app_commands.Command(
    name="trading_monitor",
    description="Start or stop trading video monitoring",
    callback=trading_monitor_command
))

bot.tree.add_command(app_commands.Command(
    name="trading_status", 
    description="Check trading video monitoring status",
    callback=trading_status_command
))

bot.tree.add_command(app_commands.Command(
    name="trading_upload",
    description="Manually upload a specific trading video", 
    callback=trading_upload_command
))

bot.tree.add_command(app_commands.Command(
    name="trading_list",
    description="List available trading videos",
    callback=trading_list_command
))
bot.tree.add_command(app_commands.Command(
    name="generate_trading_news",
    description="Generate a trading news video from analysis text",
    callback=generate_trading_news_command
))

# --- 18. VOICE-TO-VOICE CONVERSATION SYSTEM ---

# Global voice system storage
VOICE_SESSIONS = {}  # guild_id -> VoiceSession
VOICE_QUEUES = {}    # guild_id -> Queue for audio processing
TTS_ENGINES = {}     # guild_id -> TTS engine instance

# Voice configuration
VOICE_CONFIG = {
    "activation_phrase": "hey duckbot",
    "silence_threshold": 0.5,  # seconds of silence before processing
    "max_recording_duration": 30,  # max seconds to record
    "chunk_size": 1024,
    "sample_rate": 44100,
    "channels": 2
}

@dataclass
class VoiceSession:
    guild_id: int
    channel: discord.VoiceChannel
    voice_client: discord.VoiceClient
    is_listening: bool = False
    is_speaking: bool = False
    conversation_active: bool = False
    last_activity: float = field(default_factory=time.time)
    audio_queue: Queue.Queue = field(default_factory=Queue.Queue)
    recognition_thread: threading.Thread = None

class VoiceManager:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        
    def get_tts_engine(self, guild_id: int):
        """Get or create TTS engine for guild"""
        if guild_id not in TTS_ENGINES:
            engine = pyttsx3.init()
            # Configure voice settings
            voices = engine.getProperty('voices')
            if voices:
                # Try to use a pleasant voice
                for voice in voices:
                    if 'zira' in voice.name.lower() or 'david' in voice.name.lower():
                        engine.setProperty('voice', voice.id)
                        break
            engine.setProperty('rate', 180)  # Speech rate
            engine.setProperty('volume', 0.9)  # Volume level
            TTS_ENGINES[guild_id] = engine
        return TTS_ENGINES[guild_id]
    
    async def process_voice_input(self, guild_id: int, audio_data: bytes) -> str:
        """Convert voice input to text using speech recognition"""
        try:
            # Convert audio data to AudioData object
            audio_file = BytesIO(audio_data)
            with sr.AudioFile(audio_file) as source:
                audio = self.recognizer.record(source)
            
            # Recognize speech using Google's service (free tier)
            try:
                text = self.recognizer.recognize_google(audio)
                return text.lower().strip()
            except sr.RequestError:
                # Fallback to offline recognition if available
                try:
                    text = self.recognizer.recognize_sphinx(audio)
                    return text.lower().strip()
                except:
                    return None
        except Exception as e:
            print(f"Voice recognition error: {e}")
            return None
    
    async def generate_voice_response(self, guild_id: int, text: str) -> bytes:
        """Convert text to speech and return audio data"""
        try:
            engine = self.get_tts_engine(guild_id)
            
            # Create temporary file for audio output
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
                temp_path = temp_audio.name
            
            # Generate speech
            engine.save_to_file(text, temp_path)
            engine.runAndWait()
            
            # Read audio file
            with open(temp_path, 'rb') as f:
                audio_data = f.read()
            
            # Clean up
            try:
                os.unlink(temp_path)
            except Exception:
                pass
            
            return audio_data
            
        except Exception as e:
            print(f"TTS generation error: {e}")
            return None
    
    async def process_conversation(self, guild_id: int, user_input: str) -> str:
        """Process conversation using LM Studio or fallback"""
        try:
            # Try LM Studio first
            headers = {'Content-Type': 'application/json'}
            data = {
                "model": LM_STUDIO_MODEL,
                "messages": [
                    {
                        "role": "system", 
                        "content": "You are DuckBot, a helpful AI assistant in a Discord voice chat. Keep responses conversational, friendly, and under 100 words. You can help with questions, generate images, and chat naturally."
                    },
                    {"role": "user", "content": user_input}
                ],
                "temperature": 0.7,
                "max_tokens": 150
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(LM_STUDIO_URL, headers=headers, json=data, timeout=10) as response:
                    if response.status == 200:
                        result = await response.json()
                        if 'choices' in result and len(result['choices']) > 0:
                            response_text = result['choices'][0]['message']['content'].strip()
                            
                            # Track cost for voice conversation (estimated tokens)
                            input_tokens = len(user_input.split()) * 1.3
                            output_tokens = len(response_text.split()) * 1.3
                            cost_tracker.track_usage(
                                provider="lmstudio",
                                model=LM_STUDIO_MODEL or "local-model",
                                input_tokens=int(input_tokens),
                                output_tokens=int(output_tokens),
                                request_type="voice_chat"
                            )
                            
                            return response_text
            
            # Fallback responses
            fallback_responses = [
                "I heard you! That's interesting.",
                "Thanks for chatting with me!",
                "I'm here and listening.",
                "That's a great point!",
                "I appreciate you talking with me.",
                "Interesting! Tell me more.",
                "I'm processing what you said.",
                "Thanks for the conversation!"
            ]
            
            return random.choice(fallback_responses)
            
        except Exception as e:
            print(f"Conversation processing error: {e}")
            return "Sorry, I had trouble processing that. Could you try again?"

# Global voice manager
voice_manager = VoiceManager()

# --- VOICE CHANNEL COMMANDS ---

@bot.tree.command(name="voice_join", description="Join your voice channel for voice conversation")
async def voice_join_command(interaction: discord.Interaction):
    """Join user's voice channel"""
    try:
        if not interaction.user.voice:
            await interaction.response.send_message("[FAIL] You need to be in a voice channel first!", ephemeral=True)
            return
        
        channel = interaction.user.voice.channel
        guild_id = interaction.guild.id
        
        # Check if already connected
        if guild_id in VOICE_SESSIONS:
            await interaction.response.send_message(f"[EMOJI] Already connected to voice! Currently in: {VOICE_SESSIONS[guild_id].channel.name}", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        # Join voice channel
        voice_client = await channel.connect()
        
        # Create voice session
        session = VoiceSession(
            guild_id=guild_id,
            channel=channel,
            voice_client=voice_client
        )
        VOICE_SESSIONS[guild_id] = session
        VOICE_QUEUES[guild_id] = Queue.Queue()
        
        embed = discord.Embed(
            title="[EMOJI] Voice Chat Connected!",
            description=f"Joined **{channel.name}** and ready for voice conversation!",
            color=0x00ff00
        )
        embed.add_field(
            name="[EMOJI] How to Talk",
            value=f"Say **\"{VOICE_CONFIG['activation_phrase']}\"** followed by your message",
            inline=False
        )
        embed.add_field(
            name="[EMOJI][EMOJI] Voice Commands",
            value="• `/voice_leave` - Leave voice channel\\n• `/voice_status` - Check voice status\\n• `/voice_settings` - Adjust voice settings",
            inline=False
        )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await interaction.followup.send(f"[FAIL] Error joining voice: {str(e)[:100]}")

@bot.tree.command(name="join", description="Quick command to join your voice channel")
async def join_command(interaction: discord.Interaction):
    """Quick join command - alias for voice_join"""
    try:
        if not interaction.user.voice:
            await interaction.response.send_message("[FAIL] You need to be in a voice channel first!", ephemeral=True)
            return
        
        channel = interaction.user.voice.channel
        guild_id = interaction.guild.id
        
        # Check if already connected
        if guild_id in VOICE_SESSIONS:
            await interaction.response.send_message(f"[EMOJI] Already connected to voice! Currently in: {VOICE_SESSIONS[guild_id].channel.name}", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        # Join voice channel
        voice_client = await channel.connect()
        
        # Create voice session
        session = VoiceSession(
            guild_id=guild_id,
            channel=channel,
            voice_client=voice_client
        )
        VOICE_SESSIONS[guild_id] = session
        VOICE_QUEUES[guild_id] = Queue.Queue()
        
        embed = discord.Embed(
            title="[EMOJI] DuckBot Joined Voice!",
            description=f"Connected to **{channel.name}** - Ready for voice chat!",
            color=0x00ff00
        )
        embed.add_field(
            name="[EMOJI] Start Talking",
            value=f"Say **\"{VOICE_CONFIG['activation_phrase']}\"** + your message",
            inline=False
        )
        embed.add_field(
            name="[EMOJI][EMOJI] Quick Commands",
            value="• `/leave` - Leave voice\\n• `/voice_test` - Test voice\\n• `/voice_commands` - Full guide",
            inline=False
        )
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        await interaction.followup.send(f"[FAIL] Error joining voice: {str(e)[:100]}")

@bot.tree.command(name="voice_leave", description="Leave the current voice channel")
async def voice_leave_command(interaction: discord.Interaction):
    """Leave voice channel"""
    try:
        guild_id = interaction.guild.id
        
        if guild_id not in VOICE_SESSIONS:
            await interaction.response.send_message("[FAIL] Not connected to any voice channel!", ephemeral=True)
            return
        
        session = VOICE_SESSIONS[guild_id]
        
        # Disconnect from voice
        await session.voice_client.disconnect()
        
        # Cleanup
        del VOICE_SESSIONS[guild_id]
        if guild_id in VOICE_QUEUES:
            del VOICE_QUEUES[guild_id]
        if guild_id in TTS_ENGINES:
            TTS_ENGINES[guild_id].stop()
            del TTS_ENGINES[guild_id]
        
        embed = discord.Embed(
            title="[EMOJI] Voice Chat Disconnected",
            description=f"Left **{session.channel.name}** voice channel",
            color=0xff6b6b
        )
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        await interaction.response.send_message(f"[FAIL] Error leaving voice: {str(e)[:100]}")

@bot.tree.command(name="leave", description="Quick command to leave voice channel")
async def leave_command(interaction: discord.Interaction):
    """Quick leave command - alias for voice_leave"""
    try:
        guild_id = interaction.guild.id
        
        if guild_id not in VOICE_SESSIONS:
            await interaction.response.send_message("[FAIL] Not connected to any voice channel!", ephemeral=True)
            return
        
        session = VOICE_SESSIONS[guild_id]
        
        # Disconnect from voice
        await session.voice_client.disconnect()
        
        # Cleanup
        del VOICE_SESSIONS[guild_id]
        if guild_id in VOICE_QUEUES:
            del VOICE_QUEUES[guild_id]
        if guild_id in TTS_ENGINES:
            TTS_ENGINES[guild_id].stop()
            del TTS_ENGINES[guild_id]
        
        embed = discord.Embed(
            title="[EMOJI] Left Voice Channel",
            description=f"Disconnected from **{session.channel.name}**",
            color=0xff6b6b
        )
        
        await interaction.response.send_message(embed=embed)
        
    except Exception as e:
        await interaction.response.send_message(f"[FAIL] Error leaving voice: {str(e)[:100]}")

@bot.tree.command(name="voice_status", description="Check voice chat status and settings")
async def voice_status_command(interaction: discord.Interaction):
    """Check voice status"""
    try:
        guild_id = interaction.guild.id
        
        embed = discord.Embed(
            title="[EMOJI] Voice Chat Status",
            color=0x3498db
        )
        
        if guild_id in VOICE_SESSIONS:
            session = VOICE_SESSIONS[guild_id]
            embed.add_field(
                name="[EMOJI] Connection Status",
                value=f"[OK] Connected to **{session.channel.name}**",
                inline=False
            )
            embed.add_field(
                name="[EMOJI][EMOJI] Listening",
                value="[OK] Active" if session.is_listening else "⏸[EMOJI] Standby",
                inline=True
            )
            embed.add_field(
                name="[EMOJI] Speaking",
                value="[EMOJI][EMOJI] Active" if session.is_speaking else "[EMOJI] Silent",
                inline=True
            )
            embed.add_field(
                name="[EMOJI] Conversation",
                value="[EMOJI] Active" if session.conversation_active else "[EMOJI] Waiting",
                inline=True
            )
            
            # Voice settings
            embed.add_field(
                name="[SETTINGS] Voice Settings",
                value=f"**Activation:** \"{VOICE_CONFIG['activation_phrase']}\"\\n**Max Duration:** {VOICE_CONFIG['max_recording_duration']}s",
                inline=False
            )
        else:
            embed.add_field(
                name="[EMOJI] Connection Status",
                value="[FAIL] Not connected to voice",
                inline=False
            )
            embed.add_field(
                name="[TARGET] Quick Start",
                value="Use `/voice_join` to connect to your voice channel!",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        await interaction.response.send_message(f"[FAIL] Error checking voice status: {str(e)[:100]}", ephemeral=True)

@bot.tree.command(name="voice_test", description="Test voice conversation with a sample phrase")
@app_commands.describe(message="Message to convert to speech and play")
async def voice_test_command(interaction: discord.Interaction, message: str = "Hello! This is DuckBot testing voice conversation."):
    """Test voice output"""
    try:
        guild_id = interaction.guild.id
        
        if guild_id not in VOICE_SESSIONS:
            await interaction.response.send_message("[FAIL] Not connected to voice! Use `/voice_join` first.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        session = VOICE_SESSIONS[guild_id]
        
        # Generate TTS audio
        audio_data = await voice_manager.generate_voice_response(guild_id, message)
        
        if audio_data:
            # Create temporary audio file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
                temp_audio.write(audio_data)
                temp_path = temp_audio.name
            
            # Play audio in voice channel
            session.voice_client.play(discord.FFmpegPCMAudio(temp_path))
            
            embed = discord.Embed(
                title="[EMOJI] Voice Test",
                description=f"Playing: \"{message}\"",
                color=0x00ff00
            )
            
            await interaction.followup.send(embed=embed)
            
            # Cleanup after playing
            asyncio.create_task(cleanup_audio_file(temp_path, 10))  # Delete after 10 seconds
        else:
            await interaction.followup.send("[FAIL] Failed to generate voice audio")
        
    except Exception as e:
        await interaction.followup.send(f"[FAIL] Voice test error: {str(e)[:100]}")

async def cleanup_audio_file(file_path: str, delay: int):
    """Clean up temporary audio files after delay"""
    await asyncio.sleep(delay)
    try:
        os.unlink(file_path)
    except Exception:
        pass

# --- VOICE COMMANDS SYSTEM ---

@bot.tree.command(name="voice_commands", description="View available voice commands and how to use them")
async def voice_commands_help(interaction: discord.Interaction):
    """Show voice commands help"""
    try:
        embed = discord.Embed(
            title="[EMOJI] Voice Commands Guide",
            description="Learn how to use voice conversation with DuckBot!",
            color=0x9b59b6
        )
        
        embed.add_field(
            name="[EMOJI] Basic Voice Chat",
            value=f"1. Use `/voice_join` to connect\\n2. Say **\"{VOICE_CONFIG['activation_phrase']}\"**\\n3. Speak your message\\n4. DuckBot will respond with voice!",
            inline=False
        )
        
        embed.add_field(
            name="[ART] Voice Generation Commands",
            value=f"• **\"{VOICE_CONFIG['activation_phrase']} generate a sunset\"** - Create images\\n• **\"{VOICE_CONFIG['activation_phrase']} surprise me\"** - Random generation\\n• **\"{VOICE_CONFIG['activation_phrase']} start story about dragons\"** - Begin stories",
            inline=False
        )
        
        embed.add_field(
            name="[EMOJI] Conversation Examples",
            value=f"• **\"{VOICE_CONFIG['activation_phrase']} how are you?\"**\\n• **\"{VOICE_CONFIG['activation_phrase']} tell me a joke\"**\\n• **\"{VOICE_CONFIG['activation_phrase']} what can you do?\"**",
            inline=False
        )
        
        embed.add_field(
            name="[SETTINGS] Voice Settings",
            value=f"• **Max Recording:** {VOICE_CONFIG['max_recording_duration']} seconds\\n• **Activation Phrase:** \"{VOICE_CONFIG['activation_phrase']}\"\\n• **Auto-processing:** After silence",
            inline=False
        )
        
        embed.add_field(
            name="[EMOJI][EMOJI] Control Commands",
            value="• `/voice_join` - Connect to voice\\n• `/voice_leave` - Disconnect\\n• `/voice_status` - Check status\\n• `/voice_test` - Test TTS",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    except Exception as e:
        await interaction.response.send_message(f"[FAIL] Error showing voice commands: {str(e)[:100]}", ephemeral=True)

# --- VOICE EVENT HANDLERS ---

@bot.event
async def on_voice_state_update(member, before, after):
    """Handle voice state changes for voice conversation"""
    try:
        guild_id = member.guild.id
        
        # Check if DuckBot should leave when alone
        if guild_id in VOICE_SESSIONS:
            session = VOICE_SESSIONS[guild_id]
            voice_channel = session.channel
            
            # Count non-bot members in channel
            human_members = [m for m in voice_channel.members if not m.bot]
            
            # Leave if no humans in channel
            if len(human_members) == 0:
                await session.voice_client.disconnect()
                del VOICE_SESSIONS[guild_id]
                if guild_id in VOICE_QUEUES:
                    del VOICE_QUEUES[guild_id]
                print(f"[AI] Left voice channel in {member.guild.name} - no users present")
    
    except Exception as e:
        print(f"Voice state update error: {e}")

# Voice Input Detection (requires additional setup for real-time audio processing)
class VoiceInputDetector:
    def __init__(self, guild_id: int):
        self.guild_id = guild_id
        self.is_recording = False
        self.audio_buffer = BytesIO()
        self.last_speech_time = 0
        
    async def process_audio_chunk(self, data):
        """Process incoming audio chunks for voice detection"""
        try:
            # Simple voice activity detection
            audio_level = audioop.rms(data, 2)  # Get RMS level
            
            if audio_level > 500:  # Voice detected threshold
                self.last_speech_time = time.time()
                if not self.is_recording:
                    self.is_recording = True
                    self.audio_buffer = BytesIO()
                
                self.audio_buffer.write(data)
                
            elif self.is_recording and (time.time() - self.last_speech_time > VOICE_CONFIG['silence_threshold']):
                # Silence detected, process accumulated audio
                self.is_recording = False
                audio_data = self.audio_buffer.getvalue()
                
                if len(audio_data) > 8000:  # Minimum audio length
                    await self.process_voice_input(audio_data)
                
        except Exception as e:
            print(f"Audio chunk processing error: {e}")
    
    async def process_voice_input(self, audio_data: bytes):
        """Process complete voice input"""
        try:
            # Convert to text
            text = await voice_manager.process_voice_input(self.guild_id, audio_data)
            
            if text and VOICE_CONFIG['activation_phrase'] in text:
                # Remove activation phrase
                command = text.replace(VOICE_CONFIG['activation_phrase'], '').strip()
                
                if command:
                    # Process command and generate response
                    response = await voice_manager.process_conversation(self.guild_id, command)
                    
                    # Convert response to speech
                    audio_response = await voice_manager.generate_voice_response(self.guild_id, response)
                    
                    if audio_response and self.guild_id in VOICE_SESSIONS:
                        session = VOICE_SESSIONS[self.guild_id]
                        
                        # Create temporary file and play
                        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
                            temp_audio.write(audio_response)
                            temp_path = temp_audio.name
                        
                        session.voice_client.play(discord.FFmpegPCMAudio(temp_path))
                        session.is_speaking = True
                        
                        # Update user progression for voice interaction
                        # (You could track voice interactions as a new activity type)
                        
                        # Cleanup
                        asyncio.create_task(cleanup_audio_file(temp_path, 15))
        
        except Exception as e:
            print(f"Voice input processing error: {e}")

# --- 18. MESSAGE HANDLER FOR AUTO VIDEO GENERATION ---
@bot.event
async def on_message(message):
    """Handle incoming messages and auto-detect trading analysis for video generation"""
    # Ignore bot messages
    if message.author == bot.user:
        return
    
    # Auto-detect trading analysis for video generation
    if (message.channel.id == TRADING_CHANNEL_ID and 
        ("trading analysis" in message.content.lower() or 
         "crypto analysis" in message.content.lower() or
         "bitcoin" in message.content.lower() or
         "market analysis" in message.content.lower()) and
        len(message.content) > 200):  # Ensure substantial content
        
        try:
            print(f"[AI] Auto-detected trading analysis from {message.author.name}")
            print(f"[EMOJI] Triggering automatic video generation...")
            
            # Generate video from the analysis
            success = await generate_trading_video(message.content, message.channel.id)
            
            if success:
                # Send confirmation
                embed = discord.Embed(
                    title="[EMOJI] Auto-Generating Trading Video",
                    description="Detected trading analysis - creating professional news video...",
                    color=0x00ff00
                )
                embed.add_field(name="[EMOJI] Analysis Source", value=f"Message by {message.author.mention}", inline=False)
                embed.add_field(name="⏱[EMOJI] Status", value="Video generation in progress...", inline=False)
                embed.set_footer(text="Video will appear automatically when ready")
                await message.reply(embed=embed)
            else:
                await message.reply("[FAIL] Failed to generate trading video. Check ComfyUI status.")
                
        except Exception as e:
            print(f"[FAIL] Auto video generation error: {e}")
    
    # Process commands
    await bot.process_commands(message)

# --- 19. BOT STARTUP AND MAIN LOOP ---

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("[FAIL] DISCORD_TOKEN not found in environment variables")
        print("Please set DISCORD_TOKEN in your .env file")
        exit(1)
    
    print("[LAUNCH] Starting bot...")
    print("[EMOJI] DuckBot v3.1.0 VibeVoice Enhanced Edition Starting...")
    print("[EMOJI] NEW: VibeVoice Multi-Speaker TTS Integration")
    print("[EMOJI] Voice Features: 6 Professional Voices, Multi-Speaker Conversations, Free TTS")
    print("[CHART] Trading Features: AI-enhanced analysis, workflow automation")
    print("[EMOJI] Cost tracking and analytics system with voice usage monitoring")
    print("[LAUNCH] Discord slash commands: /vibevoice, /voice_presets, /voice_status")
    print("[ART] Streamlined architecture - optimized for voice synthesis")
    if VIBEVOICE_AVAILABLE:
        print("[EMOJI] VibeVoice TTS: Ready for multi-speaker voice generation")
    else:
        print("[WARN] VibeVoice TTS: Not installed (run python setup_vibevoice.py)")
    print(f"[CHART] Memory threshold: {MAX_MEMORY_THRESHOLD}%")
    print(f"[SAVE] Neo4j enabled: {NEO4J_ENABLED}")
    print(f"[EMOJI] Trading video path: {TRADING_VIDEO_PATH}")
    print(f"[EMOJI] Trading channel: {TRADING_CHANNEL_ID}")
    print("[EMOJI] Start cost dashboard separately with: python start_cost_dashboard.py")
    print("[GLOBE] Cost dashboard URL: http://localhost:8080")
    print()
    
    try:
        bot.run(DISCORD_TOKEN)
    except KeyboardInterrupt:
        print("\n[LIST] Shutting down gracefully...")
        close_neo4j()
        print("[OK] DuckBot v2.2.7 stopped successfully")
    except Exception as e:
        print(f"\n[FAIL] Critical error: {e}")
        close_neo4j()
        print("[FAIL] DuckBot v2.2.7 stopped with errors")