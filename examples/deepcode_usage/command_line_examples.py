#!/usr/bin/env python3
"""
DeepCode Command Line Usage Examples

This file demonstrates various ways to use DeepCode from the command line
interface with different configurations and use cases.
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add the DuckBot path to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from launcher_modules.deepcode.deepcode_integration import DuckBotDeepCodeIntegration


async def paper2code_basic_example():
    """Basic Paper2Code example using a research paper description."""
    print("=== Paper2Code Basic Example ===")

    # Initialize DeepCode integration
    deepcode = DuckBotDeepCodeIntegration()

    # Research paper description
    paper_description = """
    This paper presents a novel approach to sentiment analysis using transformer-based models.
    The model combines BERT architecture with attention mechanisms to achieve state-of-the-art
    performance on sentiment classification tasks. Key innovations include:
    1. Multi-lingual sentiment analysis
    2. Context-aware attention mechanisms
    3. Transfer learning capabilities
    4. Real-time sentiment prediction

    The model achieves 95% accuracy on the IMDB dataset and 92% on multi-lingual sentiment benchmarks.
    """

    # Configuration
    config = {
        "model": "qwen3-coder",
        "temperature": 0.2,
        "max_tokens": 4000,
        "output_format": "production_ready",
        "include_tests": True,
        "include_documentation": True
    }

    try:
        result = await deepcode.paper2code(
            paper_description=paper_description,
            config=config
        )

        print(f"Task ID: {result['task_id']}")
        print(f"Status: {result['status']}")
        print(f"Output directory: {result['output_path']}")

        # Monitor progress
        while True:
            status = await deepcode.get_task_status(result['task_id'])
            print(f"Progress: {status.get('progress', 0)}%")

            if status['status'] in ['completed', 'failed']:
                break

            await asyncio.sleep(2)

        if status['status'] == 'completed':
            print("✅ Paper2Code conversion completed successfully!")
            print(f"Generated files: {len(status.get('generated_files', []))}")
        else:
            print(f"❌ Paper2Code conversion failed: {status.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Error: {e}")


async def text2web_react_example():
    """Text2Web example generating a React application."""
    print("\n=== Text2Web React Example ===")

    deepcode = DuckBotDeepCodeIntegration()

    # Web application description
    web_description = """
    Create a task management web application with the following features:
    - User authentication and authorization
    - Task creation, editing, and deletion
    - Task categorization and prioritization
    - Due dates and reminders
    - Progress tracking and analytics
    - Team collaboration features
    - Responsive design for mobile and desktop
    - Dark/light theme toggle
    - Real-time notifications

    The application should use React with TypeScript, Tailwind CSS for styling,
    and a FastAPI backend with PostgreSQL database.
    """

    config = {
        "framework": "react",
        "styling": "tailwind",
        "include_auth": True,
        "include_database": True,
        "backend_framework": "fastapi",
        "database": "postgresql",
        "include_tests": True,
        "include_documentation": True
    }

    try:
        result = await deepcode.text2web(
            description=web_description,
            config=config
        )

        print(f"Task ID: {result['task_id']}")
        print(f"Status: {result['status']}")

        # Monitor progress
        while True:
            status = await deepcode.get_task_status(result['task_id'])
            print(f"Progress: {status.get('progress', 0)}% - {status.get('current_step', '')}")

            if status['status'] in ['completed', 'failed']:
                break

            await asyncio.sleep(3)

        if status['status'] == 'completed':
            print("✅ Text2Web generation completed successfully!")
            print(f"Generated {len(status.get('generated_files', []))} files")
            print("To run the application:")
            print("  cd output_directory")
            print("  npm install")
            print("  npm start")
        else:
            print(f"❌ Text2Web generation failed: {status.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Error: {e}")


async def text2backend_api_example():
    """Text2Backend example generating a REST API."""
    print("\n=== Text2Backend API Example ===")

    deepcode = DuckBotDeepCodeIntegration()

    # Backend API description
    backend_description = """
    Create a REST API for an e-commerce platform with the following endpoints:

    Products:
    - GET /api/v1/products - List all products with pagination and filtering
    - GET /api/v1/products/{id} - Get product details
    - POST /api/v1/products - Create new product
    - PUT /api/v1/products/{id} - Update product
    - DELETE /api/v1/products/{id} - Delete product

    Users:
    - POST /api/v1/auth/register - User registration
    - POST /api/v1/auth/login - User login
    - GET /api/v1/users/profile - Get user profile
    - PUT /api/v1/users/profile - Update user profile

    Orders:
    - GET /api/v1/orders - List user orders
    - POST /api/v1/orders - Create new order
    - GET /api/v1/orders/{id} - Get order details

    The API should include:
    - JWT authentication and authorization
    - Rate limiting and throttling
    - Input validation and error handling
    - Database integration with PostgreSQL
    - Caching with Redis
    - API documentation with OpenAPI/Swagger
    - Comprehensive logging and monitoring
    - Unit and integration tests
    """

    config = {
        "framework": "fastapi",
        "database": "postgresql",
        "include_auth": True,
        "include_docs": True,
        "include_tests": True,
        "include_monitoring": True,
        "include_caching": True
    }

    try:
        result = await deepcode.text2backend(
            description=backend_description,
            config=config
        )

        print(f"Task ID: {result['task_id']}")
        print(f"Status: {result['status']}")

        # Monitor progress
        while True:
            status = await deepcode.get_task_status(result['task_id'])
            print(f"Progress: {status.get('progress', 0)}%")

            if status['status'] in ['completed', 'failed']:
                break

            await asyncio.sleep(2)

        if status['status'] == 'completed':
            print("✅ Text2Backend generation completed successfully!")
            print(f"Generated {len(status.get('generated_files', []))} files")
            print("To run the API:")
            print("  cd output_directory")
            print("  pip install -r requirements.txt")
            print("  python -m uvicorn main:app --reload")
        else:
            print(f"❌ Text2Backend generation failed: {status.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Error: {e}")


async def batch_processing_example():
    """Example of batch processing multiple files."""
    print("\n=== Batch Processing Example ===")

    deepcode = DuckBotDeepCodeIntegration()

    # Multiple tasks to process
    tasks = [
        {
            "type": "paper2code",
            "description": "Research paper on machine learning optimization techniques",
            "config": {"model": "qwen3-coder", "include_tests": True}
        },
        {
            "type": "text2web",
            "description": "Simple blog application with user authentication",
            "config": {"framework": "react", "include_auth": True}
        },
        {
            "type": "text2backend",
            "description": "User management API with CRUD operations",
            "config": {"framework": "fastapi", "include_auth": True}
        }
    ]

    try:
        # Submit all tasks
        task_ids = []
        for task in tasks:
            if task["type"] == "paper2code":
                result = await deepcode.paper2code(
                    paper_description=task["description"],
                    config=task["config"]
                )
            elif task["type"] == "text2web":
                result = await deepcode.text2web(
                    description=task["description"],
                    config=task["config"]
                )
            elif task["type"] == "text2backend":
                result = await deepcode.text2backend(
                    description=task["description"],
                    config=task["config"]
                )

            task_ids.append(result['task_id'])
            print(f"Submitted {task['type']} task: {result['task_id']}")

        # Monitor all tasks
        completed_tasks = 0
        while completed_tasks < len(task_ids):
            for task_id in task_ids:
                status = await deepcode.get_task_status(task_id)
                if status['status'] == 'completed':
                    completed_tasks += 1
                    print(f"✅ Task {task_id} completed")
                elif status['status'] == 'failed':
                    completed_tasks += 1
                    print(f"❌ Task {task_id} failed: {status.get('error', 'Unknown error')}")

            print(f"Progress: {completed_tasks}/{len(task_ids)} tasks completed")
            await asyncio.sleep(3)

        print("✅ All batch processing tasks completed!")

    except Exception as e:
        print(f"❌ Error: {e}")


async def custom_template_example():
    """Example using custom templates."""
    print("\n=== Custom Template Example ===")

    deepcode = DuckBotDeepCodeIntegration()

    # Load custom template
    template_path = "config/deepcode_examples/custom_ml_template.yaml"

    # Machine learning project description
    ml_description = """
    Create a computer vision project for object detection with the following requirements:
    - Use YOLOv8 architecture for real-time object detection
    - Support for 80 COCO classes
    - Training pipeline with data augmentation
    - Evaluation metrics and visualization
    - Model export to multiple formats (ONNX, TensorRT)
    - Web interface for testing and inference
    - API for integration with other applications
    """

    try:
        result = await deepcode.generate_from_template(
            template_path=template_path,
            description=ml_description,
            config={
                "model_type": "yolov8",
                "data_source": "coco_dataset",
                "target_variable": "object_detection",
                "evaluation_metrics": ["mAP", "precision", "recall", "f1_score"],
                "deployment_method": "api_server"
            }
        )

        print(f"Task ID: {result['task_id']}")
        print(f"Status: {result['status']}")

        # Monitor progress
        while True:
            status = await deepcode.get_task_status(result['task_id'])
            print(f"Progress: {status.get('progress', 0)}%")

            if status['status'] in ['completed', 'failed']:
                break

            await asyncio.sleep(3)

        if status['status'] == 'completed':
            print("✅ Custom template generation completed successfully!")
        else:
            print(f"❌ Custom template generation failed: {status.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"❌ Error: {e}")


async def main():
    """Run all command line examples."""
    print("DeepCode Command Line Usage Examples")
    print("=" * 50)

    # Run individual examples
    await paper2code_basic_example()
    await text2web_react_example()
    await text2backend_api_example()
    await batch_processing_example()
    await custom_template_example()

    print("\n" + "=" * 50)
    print("All examples completed!")


if __name__ == "__main__":
    asyncio.run(main())