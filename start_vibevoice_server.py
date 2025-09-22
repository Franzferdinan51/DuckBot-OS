"""
VibeVoice Server Startup Script
Provides easy startup of the mock VibeVoice TTS server
"""
import asyncio
import logging
import os
import sys
import subprocess
import time
from pathlib import Path
from typing import Optional

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from vibevoice_server import app, logger
import uvicorn

def check_dependencies():
    """Check if all required dependencies are installed"""
    missing_deps = []

    try:
        import fastapi
        logger.info("[OK] FastAPI available")
    except ImportError:
        missing_deps.append("fastapi")

    try:
        import uvicorn
        logger.info("[OK] Uvicorn available")
    except ImportError:
        missing_deps.append("uvicorn")

    try:
        import edge_tts
        logger.info("[OK] Edge TTS available")
    except ImportError:
        missing_deps.append("edge-tts")

    try:
        import pyttsx3
        logger.info("[OK] pyttsx3 available")
    except ImportError:
        missing_deps.append("pyttsx3")

    try:
        from TTS.api import TTS
        logger.info("[OK] Coqui TTS available")
    except ImportError:
        missing_deps.append("TTS")

    if missing_deps:
        logger.error(f"[FAIL] Missing dependencies: {', '.join(missing_deps)}")
        logger.error("Install with: pip install " + " ".join(missing_deps))
        return False

    return True

def install_missing_dependencies():
    """Install missing dependencies"""
    missing_deps = []

    try:
        import fastapi
    except ImportError:
        missing_deps.append("fastapi")

    try:
        import uvicorn
    except ImportError:
        missing_deps.append("uvicorn")

    try:
        import pydantic
    except ImportError:
        missing_deps.append("pydantic")

    if missing_deps:
        logger.info(f"Installing missing dependencies: {', '.join(missing_deps)}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_deps)
            logger.info("[OK] Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"[FAIL] Failed to install dependencies: {e}")
            return False

    return True

def test_tts_systems():
    """Test all TTS systems"""
    logger.info("Testing TTS systems...")

    try:
        import asyncio
        import tempfile

        async def test_edge_tts():
            try:
                import edge_tts
                communicate = edge_tts.Communicate('Test message', voice='en-US-AriaNeural')
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                    temp_path = temp_file.name
                await communicate.save(temp_path)
                os.unlink(temp_path)
                logger.info("[OK] Edge TTS test passed")
                return True
            except Exception as e:
                logger.warning(f"[WARN] Edge TTS test failed: {e}")
                return False

        async def test_pyttsx3():
            try:
                import pyttsx3
                engine = pyttsx3.init()
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    temp_path = temp_file.name
                engine.save_to_file('Test message', temp_path)
                engine.runAndWait()
                os.unlink(temp_path)
                logger.info("[OK] pyttsx3 test passed")
                return True
            except Exception as e:
                logger.warning(f"[WARN] pyttsx3 test failed: {e}")
                return False

        # Run tests
        edge_ok = asyncio.run(test_edge_tts())
        pyttsx3_ok = asyncio.run(test_pyttsx3())

        if edge_ok or pyttsx3_ok:
            logger.info("[OK] At least one TTS system is working")
            return True
        else:
            logger.error("[FAIL] No TTS systems are working")
            return False

    except Exception as e:
        logger.error(f"[FAIL] TTS testing failed: {e}")
        return False

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('vibevoice_server.log'),
            logging.StreamHandler()
        ]
    )

def main():
    """Main startup function"""
    setup_logging()

    print("=" * 60)
    print("VibeVoice TTS Server - DuckBot Integration")
    print("=" * 60)

    # Check dependencies
    if not check_dependencies():
        print("\n[INFO] Installing missing dependencies...")
        if not install_missing_dependencies():
            logger.error("[FAIL] Could not install dependencies")
            return

        # Check again after installation
        if not check_dependencies():
            logger.error("[FAIL] Dependencies still missing after installation")
            return

    # Test TTS systems
    print("\n[INFO] Testing TTS systems...")
    if not test_tts_systems():
        logger.error("[FAIL] TTS systems not working")
        return

    print("\n[OK] All checks passed!")
    print("[INFO] Starting VibeVoice TTS Server...")
    print(f"[INFO] Server will be available at: http://localhost:8000")
    print("[INFO] Press Ctrl+C to stop the server")
    print("-" * 60)

    try:
        # Start the server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            access_log=True,
            reload=False
        )
    except KeyboardInterrupt:
        print("\n[INFO] Shutting down server...")
        logger.info("VibeVoice server stopped by user")
    except Exception as e:
        logger.error(f"[FAIL] Server error: {e}")
        print(f"\n[FAIL] Server error: {e}")

if __name__ == "__main__":
    main()