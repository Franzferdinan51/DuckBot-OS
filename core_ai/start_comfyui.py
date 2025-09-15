"""Compatibility shim for tests expecting start_comfyui module.

This module intentionally does not start ComfyUI; it only provides an importable
placeholder for environment checks.
"""

def is_available() -> bool:
    """Return False by default; environment may not bundle ComfyUI."""
    return False

