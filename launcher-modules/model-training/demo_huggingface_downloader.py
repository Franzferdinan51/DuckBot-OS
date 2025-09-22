#!/usr/bin/env python3
"""
Demo script for DuckBot Hugging Face Model Downloader
Demonstrates the complete functionality of the model downloading system.
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from huggingface_downloader import ModelDownloader, ModelDownloadConfig
from training_integration import TrainingModelManager

def setup_logging():
    """Setup logging for demo"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def demo_basic_download():
    """Demonstrate basic model downloading"""
    print("\n" + "="*60)
    print("DEMO 1: Basic Model Downloading")
    print("="*60)

    # Create downloader
    downloader = ModelDownloader()

    # Search for models
    print("Searching for small BERT models...")
    results = downloader.search_models("bert-base", limit=5, model_type="bert")

    if results:
        print(f"Found {len(results)} models:")
        for i, model in enumerate(results[:3], 1):
            print(f"  {i}. {model['id']} - {model.get('downloads', 0)} downloads")

        # Select first model for demo
        model_id = results[0]['id']
        print(f"\nSelected model: {model_id}")

        # Configure download
        config = ModelDownloadConfig(
            model_id=model_id,
            max_workers=2,  # Reduced for demo
            resume_download=True
        )

        # Progress callback
        def progress_callback(info):
            if isinstance(info, dict):
                if 'status' in info:
                    status = info['status']
                    if status == 'downloading':
                        progress = info.get('progress', {})
                        downloaded = progress.get('downloaded', 0)
                        total = progress.get('total', 0)
                        if total > 0:
                            percentage = (downloaded / total) * 100
                            print(f"\rDownload progress: {percentage:.1f}% ({downloaded/1024/1024:.1f}MB / {total/1024/1024:.1f}MB)", end="")
                    elif status == 'completed':
                        print(f"\n✓ Download completed: {info.get('model_id')}")
                    elif status == 'failed':
                        print(f"\n✗ Download failed: {info.get('error')}")
                else:
                    print(f"Progress info: {info}")

        print("Starting download (this may take a while for the first time)...")
        try:
            result = downloader.download_model(model_id, config, progress_callback)
            if result:
                print(f"✓ Model downloaded to: {result}")
                return result
            else:
                print("✗ Download failed")
                return None
        except Exception as e:
            print(f"✗ Download error: {e}")
            return None

    else:
        print("No models found")
        return None

def demo_training_integration():
    """Demonstrate training integration"""
    print("\n" + "="*60)
    print("DEMO 2: Training Integration")
    print("="*60)

    # Create training model manager
    manager = TrainingModelManager()

    # Download model for training
    def training_callback(info):
        status = info.get('status', 'unknown')
        if status == 'downloading':
            print(f"⏳ Downloading: {info.get('model_id')}")
        elif status == 'completed':
            print(f"✓ Ready for training: {info.get('model_id')}")
            print(f"  Path: {info.get('path')}")
        elif status == 'failed':
            print(f"✗ Training download failed: {info.get('error')}")

    print("Downloading model for training...")
    try:
        # Use a smaller model for demo
        result = manager.download_model_for_training(
            "facebook/opt-125m",
            config={"max_workers": 2},
            callback=training_callback
        )

        if result:
            print("✓ Model queued for training download")

            # Wait a bit for download to complete
            print("Waiting for download to complete...")
            time.sleep(2)

            # List available models
            available_models = manager.get_available_models()
            print(f"\nAvailable models for training: {len(available_models)}")

            for model in available_models:
                print(f"  • {model['model_id']}")
                print(f"    Format: {model['format']}")
                print(f"    Size: {model['size_mb']:.1f} MB")
                print(f"    Valid: {'✓' if model['valid'] else '✗'}")
                print(f"    Compatible: {'✓' if model['compatible'] else '✗'}")

            # Get model statistics
            stats = manager.get_model_statistics()
            print(f"\nModel Statistics:")
            print(f"  Total models: {stats['total_models']}")
            print(f"  Total size: {stats['total_size_gb']:.2f} GB")
            print(f"  Valid models: {stats['valid_models']}")
            print(f"  Queue size: {stats['queue_size']}")

        else:
            print("✗ Failed to queue model for training")

    except Exception as e:
        print(f"✗ Training integration error: {e}")

def demo_model_validation():
    """Demonstrate model validation"""
    print("\n" + "="*60)
    print("DEMO 3: Model Validation")
    print("="*60)

    from huggingface_downloader import ModelValidator

    validator = ModelValidator()

    # Check if we have any downloaded models
    manager = TrainingModelManager()
    available_models = manager.get_available_models()

    if available_models:
        model_id = available_models[0]['model_id']
        model_path = manager.get_model_path(model_id)

        if model_path:
            print(f"Validating model: {model_id}")
            print(f"Path: {model_path}")

            # Validate model structure
            validation_result = validator.validate_model_structure(model_path)

            print(f"\nValidation Results:")
            print(f"  Valid: {'✓' if validation_result['valid'] else '✗'}")

            if validation_result['issues']:
                print("  Issues:")
                for issue in validation_result['issues']:
                    print(f"    • {issue}")

            if validation_result['warnings']:
                print("  Warnings:")
                for warning in validation_result['warnings']:
                    print(f"    • {warning}")

            if validation_result['model_info']:
                print("  Model Info:")
                for key, value in validation_result['model_info'].items():
                    print(f"    {key}: {value}")

            # Check training compatibility
            print(f"\nTraining Compatibility:")
            requirements = {
                "model_type": "auto",
                "min_vocab_size": 1000,
                "max_model_size_gb": 10
            }

            compatibility_result = validator.check_model_compatibility(model_path, requirements)

            print(f"  Compatible: {'✓' if compatibility_result['compatible'] else '✗'}")

            if compatibility_result['issues']:
                print("  Issues:")
                for issue in compatibility_result['issues']:
                    print(f"    • {issue}")

            if compatibility_result['warnings']:
                print("  Warnings:")
                for warning in compatibility_result['warnings']:
                    print(f"    • {warning}")

        else:
            print("Model path not found")

    else:
        print("No models available for validation")

def demo_cache_management():
    """Demonstrate cache management"""
    print("\n" + "="*60)
    print("DEMO 4: Cache Management")
    print("="*60)

    downloader = ModelDownloader()

    # Show current cache
    cached_models = downloader.get_cached_models()
    print(f"Current cached models: {len(cached_models)}")

    if cached_models:
        print("\nCached models:")
        for model in cached_models:
            print(f"  • {model['model_id']}")
            print(f"    Revision: {model['revision']}")
            print(f"    Format: {model['format']}")
            print(f"    Size: {model['size_mb']} MB")
            print(f"    Path: {model['path']}")

    # Show cache statistics
    print(f"\nCache Statistics:")
    total_size = sum(float(model['size_mb']) for model in cached_models)
    print(f"  Total models: {len(cached_models)}")
    print(f"  Total size: {total_size:.1f} MB ({total_size/1024:.1f} GB)")

    # Demo cache clearing (optional)
    print(f"\nNote: Use clear_cache() to free up space when needed")
    print(f"  downloader.clear_cache()  # Clear all cache")
    print(f"  downloader.clear_cache('model_id')  # Clear specific model")

def demo_configuration():
    """Demonstrate configuration management"""
    print("\n" + "="*60)
    print("DEMO 5: Configuration Management")
    print("="*60)

    from huggingface_downloader import ConfigManager

    # Create config manager
    config_manager = ConfigManager()

    # Show current configuration
    print("Current Configuration:")
    config = config_manager.config

    sections = ['huggingface', 'download', 'cache', 'conversion', 'validation', 'security']
    for section in sections:
        print(f"\n  {section.upper()}:")
        for key, value in config[section].items():
            print(f"    {key}: {value}")

    # Validate configuration
    print(f"\nConfiguration Validation:")
    issues = config_manager.validate_config()

    if issues:
        print("  Issues found:")
        for issue in issues:
            print(f"    • {issue}")
    else:
        print("  ✓ Configuration is valid")

    # Show supported quantizations
    print(f"\nSupported Quantizations:")
    quantizations = config_manager.get_supported_quantizations()
    for q in quantizations:
        print(f"  • {q}")

    # Show token handling
    print(f"\nToken Configuration:")
    token = config_manager.get_huggingface_token()
    if token:
        print("  ✓ Token configured (from config or environment)")
    else:
        print("  ℹ  No token configured - public models only")
        print("    Set HUGGINGFACE_TOKEN environment variable for private models")

def run_interactive_demo():
    """Run interactive demo"""
    print("🤖 DuckBot Hugging Face Model Downloader - Interactive Demo")
    print("="*60)

    while True:
        print("\nSelect a demo:")
        print("1. Basic Model Downloading")
        print("2. Training Integration")
        print("3. Model Validation")
        print("4. Cache Management")
        print("5. Configuration Management")
        print("6. Run All Demos")
        print("0. Exit")

        choice = input("\nEnter your choice (0-6): ").strip()

        if choice == "0":
            print("👋 Goodbye!")
            break
        elif choice == "1":
            demo_basic_download()
        elif choice == "2":
            demo_training_integration()
        elif choice == "3":
            demo_model_validation()
        elif choice == "4":
            demo_cache_management()
        elif choice == "5":
            demo_configuration()
        elif choice == "6":
            print("\n🎯 Running all demos...")
            demo_basic_download()
            demo_training_integration()
            demo_model_validation()
            demo_cache_management()
            demo_configuration()
            print("\n✅ All demos completed!")
        else:
            print("❌ Invalid choice. Please try again.")

        if choice != "0":
            input("\nPress Enter to continue...")

def run_quick_demo():
    """Run a quick demo showcasing key features"""
    print("🚀 Quick Demo - Key Features Overview")
    print("="*60)

    try:
        # 1. Show configuration
        print("1. Configuration Management:")
        config_manager = ConfigManager()
        print(f"   Cache directory: {config_manager.get_cache_dir()}")
        print(f"   Max workers: {config_manager.config['huggingface']['max_workers']}")
        print(f"   Token configured: {'Yes' if config_manager.get_huggingface_token() else 'No'}")

        # 2. Show cache status
        print("\n2. Cache Status:")
        downloader = ModelDownloader()
        cached_models = downloader.get_cached_models()
        print(f"   Cached models: {len(cached_models)}")

        # 3. Show training integration
        print("\n3. Training Integration:")
        manager = TrainingModelManager()
        available_models = manager.get_available_models()
        print(f"   Available for training: {len(available_models)}")

        if available_models:
            stats = manager.get_model_statistics()
            print(f"   Total model size: {stats['total_size_gb']:.2f} GB")

        # 4. Show model search capability
        print("\n4. Model Search:")
        try:
            results = downloader.search_models("opt", limit=3)
            print(f"   Found {len(results)} 'opt' models")
            for model in results[:2]:
                print(f"   • {model['id']}")
        except Exception as e:
            print(f"   Search requires internet connection: {e}")

        print("\n✅ Demo completed successfully!")
        print("\n💡 Tips:")
        print("   • Set HUGGINGFACE_TOKEN for private models")
        print("   • Use run_interactive_demo() for detailed examples")
        print("   • Check README.md for full documentation")

    except Exception as e:
        print(f"❌ Demo error: {e}")
        print("This is normal if dependencies are missing or there's no internet connection")

def main():
    """Main entry point"""
    setup_logging()

    if len(sys.argv) > 1:
        if sys.argv[1] == "--interactive":
            run_interactive_demo()
        elif sys.argv[1] == "--quick":
            run_quick_demo()
        elif sys.argv[1] == "--help":
            print("""
DuckBot Hugging Face Model Downloader Demo

Usage:
  python demo_huggingface_downloader.py [options]

Options:
  --interactive    Run interactive demo with all features
  --quick          Run quick overview demo
  --help           Show this help message

Examples:
  python demo_huggingface_downloader.py --interactive
  python demo_huggingface_downloader.py --quick
            """)
        else:
            print("Unknown option. Use --help for usage information.")
    else:
        # Default to quick demo
        run_quick_demo()

if __name__ == "__main__":
    main()