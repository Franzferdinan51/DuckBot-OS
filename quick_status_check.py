#!/usr/bin/env python3
"""
Quick Status Check for DuckBot Services
Provides immediate snapshot of current system state
"""

import socket
import requests
import subprocess
import time
import json
from datetime import datetime

def check_port(port, description=""):
    """Check if a port is available"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('localhost', port))
            if result == 0:
                return f"[RED] Port {port} {description}: IN USE"
            else:
                return f"[GREEN] Port {port} {description}: Available"
    except Exception as e:
        return f"[YELLOW] Port {port} {description}: Error - {e}"

def check_http_endpoint(url, description=""):
    """Check HTTP endpoint availability"""
    try:
        response = requests.get(url, timeout=2)
        return f"[GREEN] {description}: HTTP {response.status_code}"
    except requests.exceptions.ConnectionError:
        return f"[RED] {description}: Connection refused"
    except requests.exceptions.Timeout:
        return f"[YELLOW] {description}: Timeout"
    except Exception as e:
        return f"[YELLOW] {description}: Error - {e}"

def check_websocket(port, description=""):
    """Check WebSocket connectivity"""
    try:
        import websockets
        import asyncio

        async def test_connection():
            try:
                uri = f"ws://localhost:{port}"
                async with websockets.connect(uri) as websocket:
                    return True
            except:
                return False

        return asyncio.run(test_connection())
    except ImportError:
        return False

def check_process(process_name):
    """Check if a process is running"""
    try:
        result = subprocess.run(['tasklist', '/FI', f'IMAGENAME eq {process_name}'],
                              capture_output=True, text=True)
        lines = result.stdout.split('\n')
        count = sum(1 for line in lines if process_name.lower() in line.lower())
        return count > 0, count
    except:
        return False, 0

def main():
    """Main status check"""
    print("=" * 60)
    print("DUCKBOT SYSTEM STATUS CHECK")
    print("=" * 60)
    print(f"Check Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Check key ports
    print("PORT STATUS:")
    ports_to_check = [
        (8791, "MCP Server"),
        (8792, "Chat Server"),
        (8793, "MCP Fallback"),
        (8787, "Enhanced WebUI"),
        (8788, "Monitoring Dashboard"),
        (3000, "React Dev Server"),
        (5000, "Development Server"),
        (8000, "VibeVoice TTS"),
        (8080, "DuckBotOS"),
        (1234, "LM Studio")
    ]

    for port, desc in ports_to_check:
        print(f"   {check_port(port, desc)}")

    print()

    # Check HTTP endpoints
    print("HTTP ENDPOINTS:")
    endpoints = [
        ("http://localhost:8787", "Enhanced WebUI"),
        ("http://localhost:8788", "Monitoring Dashboard"),
        ("http://localhost:3000", "React Dev Server"),
        ("http://localhost:5000", "Development Server")
    ]

    for url, desc in endpoints:
        print(f"   {check_http_endpoint(url, desc)}")

    print()

    # Check WebSocket connectivity
    print("WEBSOCKET CONNECTIVITY:")
    websocket_ports = [
        (8791, "MCP Server"),
        (8792, "Chat Server"),
        (8793, "MCP Fallback")
    ]

    for port, desc in websocket_ports:
        try:
            if check_websocket(port):
                print(f"   [GREEN] WebSocket {port} ({desc}): Connected")
            else:
                print(f"   [RED] WebSocket {port} ({desc}): Disconnected")
        except:
            print(f"   [YELLOW] WebSocket {port} ({desc}): Cannot test")

    print()

    # Check processes
    print("PROCESS STATUS:")
    processes = [
        ("python.exe", "Python"),
        ("python3.exe", "Python3"),
        ("electron.exe", "Electron"),
        ("node.exe", "Node.js"),
        ("chrome.exe", "Chrome"),
        ("LM Studio.exe", "LM Studio")
    ]

    for proc_name, desc in processes:
        is_running, count = check_process(proc_name)
        if is_running:
            print(f"   [GREEN] {desc}: {count} process(es) running")
        else:
            print(f"   [RED] {desc}: Not running")

    print()

    # Check for log files
    print("LOG FILES:")
    log_files = [
        "duckbot/logs/electron-error.log",
        "duckbot/react-webui/electron-error.log",
        "duckbot/logs/system.log",
        "duckbot/logs/application.log"
    ]

    for log_file in log_files:
        import os
        if os.path.exists(log_file):
            file_size = os.path.getsize(log_file)
            print(f"   [FILE] {log_file}: {file_size} bytes")
        else:
            print(f"   [MISSING] {log_file}: Not found")

    print()
    print("=" * 60)
    print("Status check completed!")
    print("INFO: Run 'python server_monitor.py' for real-time monitoring")
    print("INFO: Run 'python log_watcher.py' for real-time log monitoring")
    print("=" * 60)

if __name__ == "__main__":
    main()