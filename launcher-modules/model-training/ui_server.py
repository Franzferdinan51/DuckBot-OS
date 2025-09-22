#!/usr/bin/env python3
"""
Simple HTTP Server for DuckBot AutoTrain UI
"""

import os
import sys
import http.server
import socketserver
import webbrowser
import threading
import time
from pathlib import Path

def start_server(port=8080, open_browser=True):
    """Start the HTTP server for the AutoTrain UI"""
    
    # Get the directory containing this script
    script_dir = Path(__file__).parent
    
    # Change to the script directory
    os.chdir(script_dir)
    
    # Check if UI files exist
    ui_files = ["enhanced_autotrain_ui.html", "autotrain_ui.html", "ui.html"]
    ui_file = None
    for file in ui_files:
        if (script_dir / file).exists():
            ui_file = file
            break
    
    if not ui_file:
        print(f"Error: UI file not found. Checked: {', '.join(ui_files)}")
        return False
    
    # Define request handler
    class AutoTrainHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def end_headers(self):
            # Add CORS headers
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', '*')
            super().end_headers()
        
        def do_OPTIONS(self):
            # Handle CORS preflight requests
            self.send_response(200)
            self.end_headers()
    
    # Start server
    try:
        with socketserver.TCPServer(("", port), AutoTrainHTTPRequestHandler) as httpd:
            print(f"DuckBot AutoTrain UI Server started at http://localhost:{port}")
            print(f"Serving files from: {script_dir}")
            print(f"Main UI file: {ui_file}")
            
            # Open browser in a separate thread
            if open_browser:
                def open_browser_delayed():
                    time.sleep(1)
                    webbrowser.open(f'http://localhost:{port}/{ui_file}')
                
                browser_thread = threading.Thread(target=open_browser_delayed, daemon=True)
                browser_thread.start()
            
            print("\nPress Ctrl+C to stop the server")
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\nShutting down server...")
                httpd.shutdown()
                return True
                
    except Exception as e:
        print(f"Error starting server: {e}")
        return False

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="DuckBot AutoTrain UI Server")
    parser.add_argument("--port", type=int, default=8080, help="Port to run the server on")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    
    args = parser.parse_args()
    
    success = start_server(args.port, not args.no_browser)
    
    if success:
        print("Server stopped successfully")
        return 0
    else:
        print("Server failed to start")
        return 1

if __name__ == "__main__":
    sys.exit(main())