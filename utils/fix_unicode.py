#!/usr/bin/env python3
"""
Fix Unicode encoding issues by setting proper environment variables
"""
import os
import sys

def setup_unicode_environment():
    """Setup proper Unicode encoding for Windows console"""
    if os.name == 'nt':  # Windows
        # Set UTF-8 encoding for console output
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        
        # Enable UTF-8 mode in Python 3.7+
        if hasattr(sys, 'set_int_max_str_digits'):
            os.environ['PYTHONUTF8'] = '1'
    
    # Configure stdout/stderr encoding
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except Exception:
            pass

if __name__ == "__main__":
    setup_unicode_environment()
    print("[OK] Unicode environment configured")