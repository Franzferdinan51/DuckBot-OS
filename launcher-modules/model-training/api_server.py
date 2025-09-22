#!/usr/bin/env python3
"""
API Server for DuckBot Model Training Module
Provides REST API for integration with Electron launcher
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import time

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from model_trainer import ModelTrainer, ModelRegistry

class ModelTrainingAPIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for model training API"""
    
    def __init__(self, *args, **kwargs):
        self.module_dir = Path(__file__).parent
        super().__init__(*args, **kwargs)
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # Set CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        
        if path == '/api/models':
            self._get_models()
        elif path == '/api/projects':
            self._get_projects()
        elif path == '/api/status':
            self._get_status()
        elif path == '/api/config':
            self._get_config()
        else:
            self._send_error(404, "Not Found")
    
    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # Set CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        
        if path == '/api/projects':
            self._create_project()
        elif path == '/api/train':
            self._start_training()
        elif path == '/api/stop':
            self._stop_training()
        else:
            self._send_error(404, "Not Found")
    
    def _get_models(self):
        """Get list of available models"""
        try:
            trainer = ModelTrainer()
            models = trainer.list_available_models()
            self._send_json_response(200, models)
        except Exception as e:
            self._send_error(500, f"Failed to get models: {str(e)}")
    
    def _get_projects(self):
        """Get list of projects"""
        try:
            # In a real implementation, this would load from project storage
            projects = [
                {
                    "id": "proj-001",
                    "name": "Sample Project",
                    "model": "llama-2-7b",
                    "status": "completed",
                    "createdAt": "2023-06-15",
                    "lastTrained": "2023-06-16"
                }
            ]
            self._send_json_response(200, projects)
        except Exception as e:
            self._send_error(500, f"Failed to get projects: {str(e)}")
    
    def _get_status(self):
        """Get training status"""
        try:
            trainer = ModelTrainer()
            status = trainer.get_training_status()
            self._send_json_response(200, status)
        except Exception as e:
            self._send_error(500, f"Failed to get status: {str(e)}")
    
    def _get_config(self):
        """Get module configuration"""
        try:
            config = {
                "name": "Model Training Studio",
                "version": "1.0.0",
                "description": "Train and fine-tune AI models with GGUF and Hugging Face support",
                "features": [
                    "GGUF Model Support",
                    "Hugging Face Integration",
                    "LoRA Fine-tuning",
                    "Full Fine-tuning",
                    "Knowledge Distillation",
                    "AutoTrain-like Interface"
                ]
            }
            self._send_json_response(200, config)
        except Exception as e:
            self._send_error(500, f"Failed to get config: {str(e)}")
    
    def _create_project(self):
        """Create a new project"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            project_data = json.loads(post_data.decode('utf-8'))
            
            # In a real implementation, this would save the project
            project_data["id"] = f"proj-{int(time.time())}"
            project_data["createdAt"] = time.strftime("%Y-%m-%d")
            project_data["status"] = "created"
            
            self._send_json_response(201, project_data)
        except Exception as e:
            self._send_error(500, f"Failed to create project: {str(e)}")
    
    def _start_training(self):
        """Start model training"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            training_config = json.loads(post_data.decode('utf-8'))
            
            # In a real implementation, this would start training
            response = {
                "status": "started",
                "message": "Training started successfully",
                "config": training_config
            }
            
            self._send_json_response(200, response)
        except Exception as e:
            self._send_error(500, f"Failed to start training: {str(e)}")
    
    def _stop_training(self):
        """Stop model training"""
        try:
            trainer = ModelTrainer()
            success = trainer.stop_training()
            
            response = {
                "status": "stopped" if success else "error",
                "message": "Training stopped successfully" if success else "No training in progress"
            }
            
            self._send_json_response(200, response)
        except Exception as e:
            self._send_error(500, f"Failed to stop training: {str(e)}")
    
    def _send_json_response(self, status_code: int, data: Any):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode('utf-8'))
    
    def _send_error(self, status_code: int, message: str):
        """Send error response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        error_response = {
            "error": message,
            "status_code": status_code
        }
        self.wfile.write(json.dumps(error_response, indent=2).encode('utf-8'))

class ModelTrainingAPIServer:
    """Model Training API Server"""
    
    def __init__(self, host: str = 'localhost', port: int = 8000):
        self.host = host
        self.port = port
        self.server = None
        self.thread = None
        self.is_running = False
    
    def start(self):
        """Start the API server"""
        if self.is_running:
            print("API server is already running")
            return
        
        try:
            self.server = HTTPServer((self.host, self.port), ModelTrainingAPIHandler)
            self.is_running = True
            
            # Start server in a separate thread
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            
            print(f"Model Training API server started on http://{self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"Failed to start API server: {e}")
            return False
    
    def stop(self):
        """Stop the API server"""
        if not self.is_running:
            print("API server is not running")
            return
        
        try:
            if self.server:
                self.server.shutdown()
                self.server.server_close()
            
            self.is_running = False
            print("Model Training API server stopped")
            return True
        except Exception as e:
            print(f"Failed to stop API server: {e}")
            return False

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="DuckBot Model Training API Server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--stop", action="store_true", help="Stop the server")
    
    args = parser.parse_args()
    
    server = ModelTrainingAPIServer(args.host, args.port)
    
    if args.stop:
        server.stop()
        return
    
    if server.start():
        try:
            print("Press Ctrl+C to stop the server")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down server...")
            server.stop()

if __name__ == "__main__":
    main()