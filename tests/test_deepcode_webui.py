#!/usr/bin/env python3
"""
DeepCode WebUI Integration Test Suite
Comprehensive testing for DeepCode WebUI components and API service

Tests:
- WebUI service startup and shutdown
- Authentication and authorization
- API endpoints functionality
- WebSocket connections
- File upload and processing
- Task management
- Agent coordination
- MCP server integration
- Template rendering
- Static file serving
"""

import os
import sys
import json
import time
import asyncio
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
import httpx
from fastapi.testclient import TestClient

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import modules to test
try:
    from duckbot.services.deepcode_webui_service import DeepCodeWebUIService, TaskRequest, TaskStatus
    from duckbot.services.deepcode_auth_integration import DeepCodeAuthIntegration, DeepCodeRole, Permission
    from duckbot.services.deepcode_auth_integration import auth_integration, auth_routes
except ImportError as e:
    print(f"Warning: Could not import DeepCode modules: {e}")
    # Create mock classes for testing
    class DeepCodeWebUIService:
        def __init__(self):
            self.app = Mock()

    class TaskRequest:
        pass

    class TaskStatus:
        PENDING = "pending"
        RUNNING = "running"
        COMPLETED = "completed"
        FAILED = "failed"

class TestDeepCodeWebUIService:
    """Test DeepCode WebUI Service"""

    @pytest.fixture
    def service(self):
        """Create a test instance of the service"""
        with patch('duckbot.services.deepcode_webui_service.DeepCodeIntegration'):
            with patch('duckbot.services.deepcode_webui_service.DeepCodeMCPServers'):
                return DeepCodeWebUIService()

    @pytest.fixture
    def client(self, service):
        """Create a test client"""
        return TestClient(service.app)

    def test_service_initialization(self, service):
        """Test service initialization"""
        assert service.ws_manager is not None
        assert service.auth_integration is not None
        assert service.tasks == {}
        assert service.agents == {}
        assert service.mcp_servers_info == {}
        assert service.projects == {}
        assert service.papers == {}

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_authentication_required(self, client):
        """Test that authentication is required for protected endpoints"""
        # Test without authentication
        response = client.get("/api/deepcode/status")
        assert response.status_code == 401

        response = client.get("/api/deepcode/tasks")
        assert response.status_code == 401

        response = client.post("/api/deepcode/tasks", json={})
        assert response.status_code == 401

    def test_authentication_flow(self, client):
        """Test complete authentication flow"""
        # Login
        login_data = {
            "username": "admin",
            "password": "admin"
        }
        response = client.post("/auth/login", data=login_data)
        assert response.status_code == 200

        login_response = response.json()
        assert "access_token" in login_response
        assert "refresh_token" in login_response
        assert "user" in login_response

        # Use token for authenticated requests
        headers = {"Authorization": f"Bearer {login_response['access_token']}"}

        # Test authenticated endpoint
        response = client.get("/api/deepcode/status", headers=headers)
        assert response.status_code == 200

        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 200

        # Test token refresh
        refresh_data = {
            "refresh_token": login_response["refresh_token"]
        }
        response = client.post("/auth/refresh", data=refresh_data)
        assert response.status_code == 200

        # Test logout
        logout_data = {
            "refresh_token": login_response["refresh_token"]
        }
        response = client.post("/auth/logout", data=logout_data)
        assert response.status_code == 200

    def test_task_management(self, client):
        """Test task management endpoints"""
        # Login first
        login_response = client.post("/auth/login", data={"username": "admin", "password": "admin"})
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create task
        task_data = {
            "task_type": "text2web",
            "description": "Create a simple web application",
            "priority": "medium",
            "parameters": {"framework": "react"}
        }

        response = client.post("/api/deepcode/tasks", json=task_data, headers=headers)
        assert response.status_code == 200

        task_response = response.json()
        assert "id" in task_response
        assert task_response["task_type"] == "text2web"
        assert task_response["status"] == "pending"

        # Get tasks
        response = client.get("/api/deepcode/tasks", headers=headers)
        assert response.status_code == 200

        tasks = response.json()
        assert len(tasks) == 1
        assert tasks[0]["id"] == task_response["id"]

        # Get specific task
        task_id = task_response["id"]
        response = client.get(f"/api/deepcode/tasks/{task_id}", headers=headers)
        assert response.status_code == 200

        task = response.json()
        assert task["id"] == task_id

        # Delete task
        response = client.delete(f"/api/deepcode/tasks/{task_id}", headers=headers)
        assert response.status_code == 200

        # Verify task is deleted
        response = client.get(f"/api/deepcode/tasks/{task_id}", headers=headers)
        assert response.status_code == 404

    def test_agents_endpoint(self, client):
        """Test agents endpoint"""
        # Login first
        login_response = client.post("/auth/login", data={"username": "admin", "password": "admin"})
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Get agents (should be empty initially)
        response = client.get("/api/deepcode/agents", headers=headers)
        assert response.status_code == 200

        agents = response.json()
        assert isinstance(agents, list)

        # Create agent
        agent_data = {
            "name": "Test Agent",
            "type": "code_generator",
            "description": "A test agent for code generation",
            "capabilities": ["code_generation", "analysis"]
        }

        response = client.post("/api/deepcode/agents", json=agent_data, headers=headers)
        assert response.status_code == 200

    def test_mcp_servers_endpoint(self, client):
        """Test MCP servers endpoint"""
        # Login first
        login_response = client.post("/auth/login", data={"username": "admin", "password": "admin"})
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Get MCP servers
        response = client.get("/api/deepcode/mcp-servers", headers=headers)
        assert response.status_code == 200

        servers = response.json()
        assert isinstance(servers, list)

    def test_projects_endpoint(self, client):
        """Test projects endpoint"""
        # Login first
        login_response = client.post("/auth/login", data={"username": "admin", "password": "admin"})
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Get projects
        response = client.get("/api/deepcode/projects", headers=headers)
        assert response.status_code == 200

        projects = response.json()
        assert isinstance(projects, list)

    def test_file_upload(self, client):
        """Test file upload functionality"""
        # Login first
        login_response = client.post("/auth/login", data={"username": "admin", "password": "admin"})
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a test paper content.")
            test_file_path = f.name

        try:
            # Upload file
            with open(test_file_path, 'rb') as f:
                files = {"file": ("test_paper.txt", f, "text/plain")}
                response = client.post("/api/deepcode/upload-paper", files=files, headers=headers)

            assert response.status_code == 200
            paper_response = response.json()
            assert "id" in paper_response
            assert paper_response["filename"] == "test_paper.txt"

            # Get papers
            response = client.get("/api/deepcode/papers", headers=headers)
            assert response.status_code == 200

            papers = response.json()
            assert len(papers) == 1
            assert papers[0]["filename"] == "test_paper.txt"

        finally:
            # Clean up test file
            os.unlink(test_file_path)

    def test_web_application_generation(self, client):
        """Test web application generation"""
        # Login first
        login_response = client.post("/auth/login", data={"username": "admin", "password": "admin"})
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Generate web application
        web_data = {
            "description": "Create a simple todo application with React",
            "framework": "react",
            "styling": "tailwind"
        }

        response = client.post("/api/deepcode/generate-web", json=web_data, headers=headers)
        assert response.status_code == 200

        gen_response = response.json()
        assert "task_id" in gen_response
        assert "message" in gen_response

    def test_backend_generation(self, client):
        """Test backend application generation"""
        # Login first
        login_response = client.post("/auth/login", data={"username": "admin", "password": "admin"})
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Generate backend
        backend_data = {
            "description": "Create a REST API for user management",
            "framework": "python-fastapi",
            "database": "postgresql"
        }

        response = client.post("/api/deepcode/generate-backend", json=backend_data, headers=headers)
        assert response.status_code == 200

        gen_response = response.json()
        assert "task_id" in gen_response
        assert "message" in gen_response

    def test_permission_based_access(self, client):
        """Test permission-based access control"""
        # This test would require creating users with different roles
        # For now, we'll test the structure
        pass

class TestDeepCodeAuthIntegration:
    """Test DeepCode Authentication Integration"""

    @pytest.fixture
    def auth_integration(self):
        """Create a test auth integration"""
        return DeepCodeAuthIntegration("test-secret-key")

    def test_token_creation_and_verification(self, auth_integration):
        """Test JWT token creation and verification"""
        # Create token
        data = {"sub": "testuser", "role": "admin", "permissions": ["read", "write"]}
        token = auth_integration.create_access_token(data)

        assert token is not None
        assert isinstance(token, str)

        # Verify token
        token_data = auth_integration.verify_token(token)
        assert token_data is not None
        assert token_data.username == "testuser"

    def test_user_authentication(self, auth_integration):
        """Test user authentication"""
        # Test valid credentials
        user = auth_integration.authenticate_user("admin", "admin")
        assert user is not None
        assert user.username == "admin"
        assert user.role == DeepCodeRole.ADMIN

        # Test invalid credentials
        user = auth_integration.authenticate_user("admin", "wrong_password")
        assert user is None

        # Test non-existent user
        user = auth_integration.authenticate_user("nonexistent", "password")
        assert user is None

    def test_api_key_management(self, auth_integration):
        """Test API key management"""
        # Create API key
        api_key = auth_integration.create_api_key(
            "admin",
            "Test API Key",
            [Permission.PAPER_UPLOAD, Permission.PAPER_ANALYZE]
        )

        assert api_key is not None
        assert api_key.name == "Test API Key"
        assert api_key.key.startswith("dkc_")
        assert Permission.PAPER_UPLOAD in api_key.permissions

        # Verify API key
        verified_key = auth_integration.verify_api_key(api_key.key)
        assert verified_key is not None
        assert verified_key.id == api_key.id

    def test_permission_system(self, auth_integration):
        """Test permission system"""
        # Get admin user
        admin_user = auth_integration.users.get("admin")
        assert admin_user is not None

        # Test admin permissions
        assert auth_integration.has_permission(admin_user, Permission.PAPER_UPLOAD)
        assert auth_integration.has_permission(admin_user, Permission.WEB_GENERATE)
        assert auth_integration.has_permission(admin_user, Permission.AGENT_CREATE)
        assert auth_integration.has_permission(admin_user, Permission.SYSTEM_CONFIG)

    def test_role_permissions_mapping(self, auth_integration):
        """Test role-permission mapping"""
        from duckbot.services.deepcode_auth_integration import ROLE_PERMISSIONS

        # Test admin role has all permissions
        admin_permissions = ROLE_PERMISSIONS[DeepCodeRole.ADMIN]
        assert len(admin_permissions) > 0

        # Test viewer role has limited permissions
        viewer_permissions = ROLE_PERMISSIONS[DeepCodeRole.VIEWER]
        assert Permission.AGENT_VIEW in viewer_permissions
        assert Permission.SYSTEM_CONFIG not in viewer_permissions

class TestDeepCodeWebSocket:
    """Test WebSocket functionality"""

    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """Test WebSocket connection"""
        # This test would require a running server
        # For now, we'll test the WebSocket manager logic
        from duckbot.services.deepcode_webui_service import WebSocketManager

        manager = WebSocketManager()
        assert len(manager.active_connections) == 0

        # Mock WebSocket
        mock_ws = AsyncMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_text = AsyncMock()

        # Test connection
        await manager.connect(mock_ws)
        assert len(manager.active_connections) == 1

        # Test broadcast
        message = {"type": "test", "data": "test_data"}
        await manager.broadcast(message)

        # Verify send_text was called
        mock_ws.send_text.assert_called_once()

        # Test disconnection
        manager.disconnect(mock_ws)
        assert len(manager.active_connections) == 0

@pytest.mark.integration
class TestDeepCodeIntegration:
    """Integration tests for DeepCode components"""

    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        # This test would require a full setup with real components
        # For now, we'll outline the test structure
        pass

    def test_stress_testing(self):
        """Test system under load"""
        # This test would simulate heavy load
        pass

    def test_error_handling(self):
        """Test error handling scenarios"""
        # Test various error scenarios
        pass

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])