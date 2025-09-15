# DuckBot Unicode Encoding Fix
import sys
import os

# Force UTF-8 encoding on Windows
if sys.platform == "win32":
    # Set environment variables for Python processes
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("PYTHONUTF8", "1")
    
    # Try to reconfigure stdout/stderr for current process
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass
