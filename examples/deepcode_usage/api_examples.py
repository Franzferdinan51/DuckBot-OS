#!/usr/bin/env python3
"""
DeepCode API Usage Examples

This file demonstrates how to use DeepCode through its programmatic API
for integration into other applications and services.
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Add the DuckBot path to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from launcher_modules.deepcode.deepcode_integration import DuckBotDeepCodeIntegration
from launcher_modules.deepcode.deepcode_mcp_servers import (
    DocumentAnalysisMCPServer,
    CodeGenerationMCPServer,
    WebScaffoldingMCPServer,
    BackendGenerationMCPServer
)


class DeepCodeAPIClient:
    """High-level API client for DeepCode integration."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the DeepCode API client."""
        self.deepcode = DuckBotDeepCodeIntegration()
        self.config = config or {}

    async def paper_to_code(
        self,
        paper_content: str,
        output_path: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Convert research paper to production-ready code.

        Args:
            paper_content: Content or description of the research paper
            output_path: Optional output directory path
            **kwargs: Additional configuration options

        Returns:
            Dictionary containing task information and status
        """
        config = {**self.config, **kwargs}

        result = await self.deepcode.paper2code(
            paper_description=paper_content,
            config=config
        )

        if output_path:
            result['output_path'] = output_path

        return result

    async def text_to_web(
        self,
        description: str,
        framework: str = "react",
        output_path: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate complete web application from text description.

        Args:
            description: Natural language description of the web application
            framework: Target framework (react, vue, angular, etc.)
            output_path: Optional output directory path
            **kwargs: Additional configuration options

        Returns:
            Dictionary containing task information and status
        """
        config = {**self.config, "framework": framework, **kwargs}

        result = await self.deepcode.text2web(
            description=description,
            config=config
        )

        if output_path:
            result['output_path'] = output_path

        return result

    async def text_to_backend(
        self,
        description: str,
        framework: str = "fastapi",
        output_path: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate backend system from text description.

        Args:
            description: Natural language description of the backend system
            framework: Target framework (fastapi, flask, django, etc.)
            output_path: Optional output directory path
            **kwargs: Additional configuration options

        Returns:
            Dictionary containing task information and status
        """
        config = {**self.config, "framework": framework, **kwargs}

        result = await self.deepcode.text2backend(
            description=description,
            config=config
        )

        if output_path:
            result['output_path'] = output_path

        return result

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get the status of a specific task.

        Args:
            task_id: ID of the task to check

        Returns:
            Dictionary containing task status information
        """
        return await self.deepcode.get_task_status(task_id)

    async def wait_for_completion(self, task_id: str, timeout: int = 300) -> Dict[str, Any]:
        """Wait for a task to complete.

        Args:
            task_id: ID of the task to wait for
            timeout: Maximum time to wait in seconds

        Returns:
            Dictionary containing final task status
        """
        start_time = asyncio.get_event_loop().time()

        while True:
            status = await self.get_task_status(task_id)

            if status['status'] in ['completed', 'failed']:
                return status

            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError(f"Task {task_id} timed out after {timeout} seconds")

            await asyncio.sleep(2)

    async def list_tasks(self, limit: int = 10) -> list:
        """List recent tasks.

        Args:
            limit: Maximum number of tasks to return

        Returns:
            List of task information
        """
        # This would need to be implemented in the DeepCode integration
        # For now, return empty list
        return []

    async def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """Cancel a running task.

        Args:
            task_id: ID of the task to cancel

        Returns:
            Dictionary containing cancellation status
        """
        # This would need to be implemented in the DeepCode integration
        # For now, return mock response
        return {"task_id": task_id, "cancelled": True}


class DeepCodeMCPClient:
    """MCP (Model Context Protocol) client for DeepCode."""

    def __init__(self):
        """Initialize the MCP client."""
        self.document_server = DocumentAnalysisMCPServer()
        self.code_server = CodeGenerationMCPServer()
        self.web_server = WebScaffoldingMCPServer()
        self.backend_server = BackendGenerationMCPServer()

    async def analyze_document(self, document_path: str) -> Dict[str, Any]:
        """Analyze a document using MCP.

        Args:
            document_path: Path to the document to analyze

        Returns:
            Document analysis results
        """
        return await self.document_server.analyze_document(document_path)

    async def generate_code(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code using MCP.

        Args:
            prompt: Code generation prompt
            context: Context information for code generation

        Returns:
            Generated code and metadata
        """
        return await self.code_server.generate_code(prompt, context)

    async def scaffold_web(self, description: str, framework: str) -> Dict[str, Any]:
        """Scaffold web application using MCP.

        Args:
            description: Application description
            framework: Target framework

        Returns:
            Scaffolded web application structure
        """
        return await self.web_server.scaffold_application(description, framework)

    async def generate_backend(self, description: str, architecture: str) -> Dict[str, Any]:
        """Generate backend system using MCP.

        Args:
            description: Backend system description
            architecture: Target architecture pattern

        Returns:
            Generated backend system structure
        """
        return await self.backend_server.generate_backend(description, architecture)


async def basic_api_usage_example():
    """Basic API usage example."""
    print("=== Basic API Usage Example ===")

    client = DeepCodeAPIClient()

    # Paper2Code example
    paper_content = """
    This paper introduces a new algorithm for natural language processing that combines
    transformer architectures with attention mechanisms. The algorithm achieves state-of-the-art
    performance on multiple benchmarks including GLUE and SQuAD.
    """

    try:
        result = await client.paper_to_code(
            paper_content=paper_content,
            include_tests=True,
            include_documentation=True
        )

        print(f"Task ID: {result['task_id']}")
        print(f"Status: {result['status']}")

        # Wait for completion
        final_status = await client.wait_for_completion(result['task_id'])
        print(f"Final status: {final_status['status']}")

        if final_status['status'] == 'completed':
            print("✅ Paper2Code completed successfully!")
        else:
            print(f"❌ Paper2Code failed: {final_status.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Error: {e}")


async def web_app_generation_example():
    """Web application generation example."""
    print("\n=== Web Application Generation Example ===")

    client = DeepCodeAPIClient()

    web_description = """
    Create a weather dashboard application with the following features:
    - Current weather display for multiple cities
    - 7-day weather forecast
    - Interactive maps with weather layers
    - Weather alerts and notifications
    - Historical weather data visualization
    - User preferences and saved locations
    - Responsive design for mobile and desktop
    - Dark/light theme toggle
    """

    try:
        result = await client.text_to_web(
            description=web_description,
            framework="react",
            include_auth=True,
            include_database=True,
            output_path="./weather_dashboard"
        )

        print(f"Task ID: {result['task_id']}")
        print(f"Output path: {result.get('output_path', 'Not specified')}")

        # Wait for completion
        final_status = await client.wait_for_completion(result['task_id'], timeout=600)
        print(f"Final status: {final_status['status']}")

        if final_status['status'] == 'completed':
            print("✅ Web application generated successfully!")
            print(f"Generated files: {len(final_status.get('generated_files', []))}")
        else:
            print(f"❌ Web application generation failed: {final_status.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Error: {e}")


async def backend_api_generation_example():
    """Backend API generation example."""
    print("\n=== Backend API Generation Example ===")

    client = DeepCodeAPIClient()

    backend_description = """
    Create a blog management API with the following endpoints and features:

    Content Management:
    - CRUD operations for blog posts
    - Category and tag management
    - Comment system with moderation
    - User roles and permissions
    - Content scheduling and publishing
    - SEO optimization features
    - Image and media upload
    - Content versioning

    User Management:
    - User registration and authentication
    - Profile management
    - Role-based access control
    - Social login integration
    - Email verification and password reset

    Analytics:
    - Post views and engagement tracking
    - User behavior analytics
    - Performance metrics
    - SEO performance tracking

    The API should include:
    - RESTful design principles
    - JWT authentication
    - Rate limiting
    - Input validation
    - Error handling
    - OpenAPI documentation
    - Comprehensive logging
    - Unit and integration tests
    """

    try:
        result = await client.text_to_backend(
            description=backend_description,
            framework="fastapi",
            include_auth=True,
            include_docs=True,
            include_tests=True,
            include_monitoring=True,
            output_path="./blog_api"
        )

        print(f"Task ID: {result['task_id']}")

        # Wait for completion
        final_status = await client.wait_for_completion(result['task_id'], timeout=600)
        print(f"Final status: {final_status['status']}")

        if final_status['status'] == 'completed':
            print("✅ Backend API generated successfully!")
            print(f"Generated {len(final_status.get('generated_files', []))} files")
        else:
            print(f"❌ Backend API generation failed: {final_status.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Error: {e}")


async def mcp_server_example():
    """MCP server usage example."""
    print("\n=== MCP Server Usage Example ===")

    client = DeepCodeMCPClient()

    try:
        # Document analysis example
        document_path = "example_paper.pdf"
        analysis = await client.analyze_document(document_path)
        print(f"Document analysis: {analysis}")

        # Code generation example
        code_prompt = "Create a Python function to calculate Fibonacci numbers"
        context = {"language": "python", "style": "functional"}
        code_result = await client.generate_code(code_prompt, context)
        print(f"Generated code: {code_result}")

        # Web scaffolding example
        web_desc = "Simple todo application with drag and drop"
        web_result = await client.scaffold_web(web_desc, "react")
        print(f"Web scaffold: {web_result}")

        # Backend generation example
        backend_desc = "User management system with roles and permissions"
        backend_result = await client.generate_backend(backend_desc, "microservices")
        print(f"Backend structure: {backend_result}")

    except Exception as e:
        print(f"❌ Error: {e}")


async def batch_processing_api_example():
    """Batch processing using API."""
    print("\n=== Batch Processing API Example ===")

    client = DeepCodeAPIClient()

    # Define batch tasks
    tasks = [
        {
            "type": "paper2code",
            "content": "Research paper on computer vision using CNNs",
            "config": {"include_tests": True}
        },
        {
            "type": "text2web",
            "content": "E-commerce product catalog with search and filters",
            "config": {"framework": "vue", "include_auth": True}
        },
        {
            "type": "text2backend",
            "content": "Inventory management system with REST API",
            "config": {"framework": "fastapi", "include_docs": True}
        }
    ]

    try:
        # Submit all tasks
        task_results = []
        for task in tasks:
            if task["type"] == "paper2code":
                result = await client.paper_to_code(
                    task["content"],
                    **task["config"]
                )
            elif task["type"] == "text2web":
                result = await client.text_to_web(
                    task["content"],
                    **task["config"]
                )
            elif task["type"] == "text2backend":
                result = await client.text_to_backend(
                    task["content"],
                    **task["config"]
                )

            task_results.append(result)
            print(f"Submitted task: {result['task_id']}")

        # Wait for all tasks to complete
        completed_tasks = 0
        while completed_tasks < len(task_results):
            for result in task_results:
                if 'final_status' not in result:
                    try:
                        status = await client.get_task_status(result['task_id'])
                        if status['status'] in ['completed', 'failed']:
                            result['final_status'] = status
                            completed_tasks += 1
                            print(f"Task {result['task_id']}: {status['status']}")
                    except:
                        pass

            print(f"Progress: {completed_tasks}/{len(task_results)} tasks completed")
            await asyncio.sleep(3)

        print("✅ All batch tasks completed!")

        # Summary
        success_count = sum(1 for r in task_results if r.get('final_status', {}).get('status') == 'completed')
        print(f"Successful tasks: {success_count}/{len(task_results)}")

    except Exception as e:
        print(f"❌ Error: {e}")


async def error_handling_example():
    """Error handling example."""
    print("\n=== Error Handling Example ===")

    client = DeepCodeAPIClient()

    # Test with invalid input
    try:
        result = await client.paper_to_code("")
        print("❌ Should have failed with empty input")
    except Exception as e:
        print(f"✅ Correctly handled error: {e}")

    # Test with invalid framework
    try:
        result = await client.text_to_web(
            "Test description",
            framework="invalid_framework"
        )
        print("❌ Should have failed with invalid framework")
    except Exception as e:
        print(f"✅ Correctly handled error: {e}")

    # Test timeout
    try:
        result = await client.wait_for_completion("invalid_task_id", timeout=5)
        print("❌ Should have timed out")
    except TimeoutError as e:
        print(f"✅ Correctly handled timeout: {e}")


async def main():
    """Run all API examples."""
    print("DeepCode API Usage Examples")
    print("=" * 50)

    await basic_api_usage_example()
    await web_app_generation_example()
    await backend_api_generation_example()
    await mcp_server_example()
    await batch_processing_api_example()
    await error_handling_example()

    print("\n" + "=" * 50)
    print("All API examples completed!")


if __name__ == "__main__":
    asyncio.run(main())