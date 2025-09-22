#!/usr/bin/env python3
"""
Test script for the Model Training API Server
"""

import requests
import json
import time
import threading

def test_api_server():
    """Test the API server endpoints"""
    base_url = "http://localhost:8000"
    
    print("Testing Model Training API Server")
    print("=" * 40)
    
    try:
        # Test config endpoint
        print("Testing /api/config endpoint...")
        response = requests.get(f"{base_url}/api/config")
        if response.status_code == 200:
            config = response.json()
            print(f"OK Config: {config['name']} v{config['version']}")
        else:
            print(f"X Config endpoint failed with status {response.status_code}")
            return False
        
        # Test models endpoint
        print("Testing /api/models endpoint...")
        response = requests.get(f"{base_url}/api/models")
        if response.status_code == 200:
            models = response.json()
            print(f"OK Models: Found {len(models)} models")
        else:
            print(f"X Models endpoint failed with status {response.status_code}")
            return False
        
        # Test projects endpoint
        print("Testing /api/projects endpoint...")
        response = requests.get(f"{base_url}/api/projects")
        if response.status_code == 200:
            projects = response.json()
            print(f"OK Projects: Found {len(projects)} projects")
        else:
            print(f"X Projects endpoint failed with status {response.status_code}")
            return False
        
        # Test status endpoint
        print("Testing /api/status endpoint...")
        response = requests.get(f"{base_url}/api/status")
        if response.status_code == 200:
            status = response.json()
            print(f"OK Status: is_training = {status.get('is_training', False)}")
        else:
            print(f"X Status endpoint failed with status {response.status_code}")
            return False
        
        # Test create project
        print("Testing POST /api/projects endpoint...")
        project_data = {
            "name": "Test Project",
            "model": "llama-2-7b"
        }
        response = requests.post(f"{base_url}/api/projects", json=project_data)
        if response.status_code == 201:
            project = response.json()
            print(f"OK Created project: {project['name']} (ID: {project['id']})")
        else:
            print(f"X Create project failed with status {response.status_code}")
            return False
        
        print("\nAll API tests passed!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("X Could not connect to API server. Make sure it's running on port 8000.")
        return False
    except Exception as e:
        print(f"X API test failed: {e}")
        return False

def main():
    """Main entry point"""
    success = test_api_server()
    
    if success:
        print("\n🎉 All API tests completed successfully!")
        return 0
    else:
        print("\n❌ Some API tests failed!")
        return 1

if __name__ == "__main__":
    exit(main())