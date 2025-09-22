#!/usr/bin/env python3
"""
Real-time Log Watcher for DuckBot Electron Launcher
Monitors log files and displays new entries in real-time
"""

import os
import time
import re
from datetime import datetime
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LogWatcher:
    def __init__(self, log_paths):
        self.log_paths = log_paths
        self.file_positions = {}
        self.running = True
        self.patterns = {
            'port_conflict': re.compile(r'Port \d+ already in use|Port \d+ already allocated'),
            'port_allocation': re.compile(r'Attempting to allocate port|Found available port|Successfully allocated'),
            'process_cleanup': re.compile(r'Successfully killed process|Attempting to cleanup'),
            'websocket_error': re.compile(r'WebSocket|MCP.*failed|WebSocket.*error'),
            'service_start': re.compile(r'Starting.*service|Starting.*server'),
            'service_error': re.compile(r'service.*failed|server.*exited|exited with code'),
            'health_check': re.compile(r'health.*check|health.*monitor'),
            'fallback': re.compile(r'fallback.*port|port.*fallback'),
            'error': re.compile(r'ERROR|Error|error'),
            'warning': re.compile(r'WARNING|Warning|warning'),
            'success': re.compile(r'successfully|successfully|✅|🟢')
        }

    def get_file_position(self, filepath):
        """Get the current file position"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(0, 2)  # Go to end of file
                return f.tell()
        except FileNotFoundError:
            return 0
        except Exception as e:
            logger.error(f"Error getting file position for {filepath}: {e}")
            return 0

    def watch_logs(self):
        """Watch all log files for new content"""
        logger.info("👀 Starting log watcher...")
        logger.info(f"📁 Watching {len(self.log_paths)} log files:")

        for path in self.log_paths:
            if os.path.exists(path):
                self.file_positions[path] = self.get_file_position(path)
                logger.info(f"   📄 {path}")
            else:
                logger.info(f"   ❌ {path} (not found)")

        logger.info("=" * 60)
        logger.info("📋 LOG WATCHER ACTIVATED - Waiting for new log entries...")
        logger.info("=" * 60)

        try:
            while self.running:
                for filepath in self.file_positions:
                    try:
                        self.check_file_updates(filepath)
                    except Exception as e:
                        logger.error(f"Error checking {filepath}: {e}")

                time.sleep(0.5)  # Check every 500ms

        except KeyboardInterrupt:
            logger.info("🛑 Log watcher stopped")

    def check_file_updates(self, filepath):
        """Check for updates in a specific file"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                current_pos = self.file_positions[filepath]
                f.seek(current_pos)
                new_content = f.read()

                if new_content:
                    # Process each new line
                    lines = new_content.strip().split('\n')
                    for line in lines:
                        if line.strip():
                            self.process_log_line(line, filepath)

                    # Update position
                    self.file_positions[filepath] = f.tell()

        except FileNotFoundError:
            # File might be created later
            pass
        except Exception as e:
            logger.error(f"Error reading {filepath}: {e}")

    def process_log_line(self, line, filepath):
        """Process a single log line"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        filename = os.path.basename(filepath)

        # Color code different types of messages
        message_type = None
        for category, pattern in self.patterns.items():
            if pattern.search(line):
                message_type = category
                break

        # Format and display the message
        if message_type == 'error':
            logger.error(f"🔴 [{timestamp}] {filename}: {line}")
        elif message_type == 'warning':
            logger.warning(f"🟡 [{timestamp}] {filename}: {line}")
        elif message_type == 'success':
            logger.info(f"🟢 [{timestamp}] {filename}: {line}")
        elif message_type == 'port_conflict':
            logger.info(f"🔴 [{timestamp}] {filename}: PORT CONFLICT - {line}")
        elif message_type == 'port_allocation':
            logger.info(f"🔌 [{timestamp}] {filename}: PORT ALLOCATION - {line}")
        elif message_type == 'process_cleanup':
            logger.info(f"🧹 [{timestamp}] {filename}: PROCESS CLEANUP - {line}")
        elif message_type == 'websocket_error':
            logger.warning(f"🌐 [{timestamp}] {filename}: WEBSOCKET ERROR - {line}")
        elif message_type == 'service_start':
            logger.info(f"🚀 [{timestamp}] {filename}: SERVICE START - {line}")
        elif message_type == 'service_error':
            logger.error(f"💥 [{timestamp}] {filename}: SERVICE ERROR - {line}")
        elif message_type == 'health_check':
            logger.info(f"❤️ [{timestamp}] {filename}: HEALTH CHECK - {line}")
        elif message_type == 'fallback':
            logger.info(f"🔄 [{timestamp}] {filename}: FALLBACK - {line}")
        else:
            logger.info(f"📝 [{timestamp}] {filename}: {line}")

    def stop(self):
        """Stop the log watcher"""
        self.running = False

def main():
    """Main function"""
    # Define log paths to watch
    log_paths = [
        "C:\\Users\\Ryan\\Desktop\\DuckBot-Consolidated-v4.2\\duckbot\\logs\\electron-error.log",
        "C:\\Users\\Ryan\\Desktop\\DuckBot-Consolidated-v4.2\\duckbot\\react-webui\\electron-error.log",
        "C:\\Users\\Ryan\\Desktop\\DuckBot-Consolidated-v4.2\\duckbot\\logs\\system.log",
        "C:\\Users\\Ryan\\Desktop\\DuckBot-Consolidated-v4.2\\logs\\application.log"
    ]

    watcher = LogWatcher(log_paths)

    try:
        watcher.watch_logs()
    except KeyboardInterrupt:
        watcher.stop()
        logger.info("👋 Log watcher stopped gracefully")

if __name__ == "__main__":
    main()