# duckbot/rate_limit.py
import time
import threading
from typing import Dict, Tuple, Optional
from fastapi import Request, HTTPException, Depends
from functools import wraps

class TokenBucket:
    """Thread-safe token bucket for rate limiting"""
    
    def __init__(self, tokens_per_second: float, burst_capacity: int):
        self.tokens_per_second = tokens_per_second
        self.burst_capacity = burst_capacity
        self.tokens = float(burst_capacity)
        self.last_refill = time.time()
        self.lock = threading.RLock()
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens. Returns True if successful."""
        with self.lock:
            now = time.time()
            elapsed = now - self.last_refill
            
            # Refill tokens based on elapsed time
            new_tokens = elapsed * self.tokens_per_second
            self.tokens = min(self.burst_capacity, self.tokens + new_tokens)
            self.last_refill = now
            
            # Try to consume tokens
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

# Global rate limiter storage
_rate_limiters: Dict[str, TokenBucket] = {}
_limiter_lock = threading.RLock()

def get_rate_limiter(key: str, tokens_per_second: float, burst_capacity: int) -> TokenBucket:
    """Get or create a rate limiter for a key"""
    with _limiter_lock:
        if key not in _rate_limiters:
            _rate_limiters[key] = TokenBucket(tokens_per_second, burst_capacity)
        return _rate_limiters[key]

def get_client_key(request: Request, token: Optional[str] = None) -> str:
    """Generate a client key for rate limiting (token or IP fallback)"""
    if token and len(token) > 10:  # Use token if available
        return f"token:{hash(token) % 1000000}"
    
    # Fallback to IP address
    client_ip = request.client.host if request.client else "unknown"
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    
    return f"ip:{client_ip}"

def rate_limited(requests_per_second: float = 5.0, burst: int = 8):
    """Decorator for rate limiting FastAPI endpoints"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from args/kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                # Look in kwargs
                request = kwargs.get('request')
            
            if not request:
                # If no request found, allow through (might be a test or direct call)
                return await func(*args, **kwargs)
            
            # Get client identifier
            token = request.headers.get("authorization", "").replace("Bearer ", "") or \
                   request.query_params.get("token")
            
            client_key = get_client_key(request, token)
            limiter = get_rate_limiter(client_key, requests_per_second, burst)
            
            if not limiter.consume():
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "Rate limit exceeded",
                        "limit": f"{requests_per_second} requests per second",
                        "burst": f"{burst} burst capacity",
                        "retry_after": 1.0 / requests_per_second
                    }
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Cleanup old rate limiters periodically
def cleanup_old_limiters():
    """Remove inactive rate limiters to prevent memory leaks"""
    current_time = time.time()
    with _limiter_lock:
        keys_to_remove = []
        for key, limiter in _rate_limiters.items():
            # Remove limiters inactive for more than 1 hour
            if current_time - limiter.last_refill > 3600:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del _rate_limiters[key]
        
        if keys_to_remove:
            print(f"Cleaned up {len(keys_to_remove)} inactive rate limiters")

# Simple dependency for getting client key in FastAPI
async def get_client_identifier(request: Request) -> str:
    """FastAPI dependency to get client identifier"""
    token = request.headers.get("authorization", "").replace("Bearer ", "") or \
           request.query_params.get("token")
    return get_client_key(request, token)