#!/usr/bin/env python3
"""
Web UI Server for DuckBot Model Training Module
"""

import os
import sys
from pathlib import Path
import argparse
from http.server import HTTPServer, SimpleHTTPRequestHandler
import webbrowser
import threading
import time

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class ModelTrainingHTTPRequestHandler(SimpleHTTPRequestHandler):
    """Custom HTTP request handler for model training UI"""
    
    def __init__(self, *args, **kwargs):
        self.module_dir = Path(__file__).parent
        super().__init__(*args, directory=str(self.module_dir), **kwargs)
    
    def end_headers(self):
        """Add CORS headers"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS"""
        self.send_response(200)
        self.end_headers()

def start_web_server(port=8080, open_browser=True):
    """Start the web server for the model training UI"""
    module_dir = Path(__file__).parent
    ui_files = [
        module_dir / "autotrain_ui.html",
        module_dir / "ui.html"
    ]
    
    ui_file = None
    for file in ui_files:
        if file.exists():
            ui_file = file
            break
    
    if not ui_file:
        print(f"Error: UI file not found. Checked: {', '.join(str(f) for f in ui_files)}")
        return False
    
    # Change to module directory
    os.chdir(module_dir)
    
    # Start server
    server_address = ('localhost', port)
    httpd = HTTPServer(server_address, ModelTrainingHTTPRequestHandler)
    
    print(f"Starting DuckBot Model Training UI server on http://localhost:{port}")
    print(f"Serving files from: {module_dir}")
    print(f"UI file: {ui_file.name}")
    
    # Open browser in a separate thread
    if open_browser:
        def open_browser_delayed():
            time.sleep(1)
            webbrowser.open(f'http://localhost:{port}/{ui_file.name}')
        
        browser_thread = threading.Thread(target=open_browser_delayed, daemon=True)
        browser_thread.start()
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.shutdown()
        return True

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="DuckBot Model Training UI Server")
    parser.add_argument("--port", type=int, default=8080, help="Port to run the server on")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    
    args = parser.parse_args()
    
    start_web_server(args.port, not args.no_browser)

if __name__ == "__main__":
    main()