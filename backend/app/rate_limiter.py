"""
Rate limiting middleware for Synapse AI API
Implements in-memory rate limiting with configurable rules per endpoint.
"""

import time
import asyncio
from typing import Dict, Tuple, Optional
from fastapi import Request, HTTPException, status
from collections import defaultdict, deque
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self):
        # Store requests as: {(client_ip, endpoint): deque(timestamps)}
        self.request_history: Dict[Tuple[str, str], deque] = defaultdict(deque)
        # Cleanup task to remove old entries
        self._last_cleanup = time.time()
        self._cleanup_interval = 300  # 5 minutes
        
        # Rate limiting rules: {endpoint_pattern: (requests_per_minute, requests_per_hour)}
        self.rate_limits = {
            # Authentication endpoints - stricter limits
            "POST:/auth/register": (5, 20),
            "POST:/auth/login": (10, 50),
            "POST:/auth/forgot-password": (3, 10),
            "POST:/auth/reset-password": (3, 10),
            
            # Core API endpoints - moderate limits
            "POST:/optimize": (20, 100),
            "POST:/execute": (30, 150),
            
            # User management - moderate limits
            "PUT:/users/profile": (10, 50),
            "PUT:/users/password": (5, 20),
            "DELETE:/users/account": (2, 5),
            
            # API key management - strict limits
            "POST:/users/api-keys": (5, 20),
            "DELETE:/users/api-keys/*": (10, 30),
            
            # Billing and payments - moderate limits
            "POST:/stripe/create-checkout": (10, 40),
            "POST:/stripe/customer-portal": (5, 20),
            
            # Default limits for all other endpoints
            "*": (60, 300)  # 60 per minute, 300 per hour
        }
    
    def get_client_identifier(self, request: Request) -> str:
        """Get unique client identifier."""
        # Try to get real IP from headers (for proxy setups)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP if there are multiple
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"
    
    def get_endpoint_key(self, method: str, path: str) -> str:
        """Get endpoint key for rate limiting rules."""
        endpoint = f"{method}:{path}"
        
        # Check for exact match first
        if endpoint in self.rate_limits:
            return endpoint
            
        # Check for wildcard patterns
        for pattern in self.rate_limits:
            if pattern.endswith("/*"):
                prefix = pattern[:-2]
                if endpoint.startswith(prefix):
                    return pattern
                    
        # Return default pattern
        return "*"
    
    def cleanup_old_entries(self):
        """Remove old request entries to prevent memory leaks."""
        current_time = time.time()
        
        # Only cleanup every 5 minutes
        if current_time - self._last_cleanup < self._cleanup_interval:
            return
            
        self._last_cleanup = current_time
        cutoff_time = current_time - 3600  # Remove entries older than 1 hour
        
        # Clean up old entries
        keys_to_remove = []
        for key, timestamps in self.request_history.items():
            # Remove timestamps older than 1 hour
            while timestamps and timestamps[0] < cutoff_time:
                timestamps.popleft()
            
            # If deque is empty, mark key for removal
            if not timestamps:
                keys_to_remove.append(key)
        
        # Remove empty keys
        for key in keys_to_remove:
            del self.request_history[key]
    
    def is_rate_limited(self, client_id: str, endpoint: str) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Check if client is rate limited for the endpoint.
        Returns (is_limited, error_message, retry_after_seconds)
        """
        current_time = time.time()
        key = (client_id, endpoint)
        
        # Get rate limits for this endpoint
        endpoint_key = self.get_endpoint_key(*endpoint.split(":", 1))
        per_minute_limit, per_hour_limit = self.rate_limits.get(endpoint_key, self.rate_limits["*"])
        
        # Get request history for this client/endpoint
        timestamps = self.request_history[key]
        
        # Remove timestamps older than 1 hour
        while timestamps and timestamps[0] < current_time - 3600:
            timestamps.popleft()
        
        # Count requests in last hour and last minute
        hour_ago = current_time - 3600
        minute_ago = current_time - 60
        
        requests_last_hour = sum(1 for ts in timestamps if ts > hour_ago)
        requests_last_minute = sum(1 for ts in timestamps if ts > minute_ago)
        
        # Check rate limits
        if requests_last_minute >= per_minute_limit:
            return True, f"Rate limit exceeded: {per_minute_limit} requests per minute", 60
        
        if requests_last_hour >= per_hour_limit:
            # Calculate when the oldest request in the hour will expire
            oldest_in_hour = next((ts for ts in timestamps if ts > hour_ago), current_time)
            retry_after = int((oldest_in_hour + 3600) - current_time)
            return True, f"Rate limit exceeded: {per_hour_limit} requests per hour", retry_after
        
        return False, None, None
    
    def record_request(self, client_id: str, endpoint: str):
        """Record a new request."""
        key = (client_id, endpoint)
        self.request_history[key].append(time.time())
        
        # Periodic cleanup
        self.cleanup_old_entries()

# Global rate limiter instance
rate_limiter = RateLimiter()

async def rate_limit_middleware(request: Request):
    """FastAPI dependency for rate limiting."""
    # Skip rate limiting for health checks and static files
    if request.url.path in ["/healthz", "/health/db", "/docs", "/openapi.json"]:
        return
    
    client_id = rate_limiter.get_client_identifier(request)
    endpoint = f"{request.method}:{request.url.path}"
    
    # Check rate limit
    is_limited, error_message, retry_after = rate_limiter.is_rate_limited(client_id, endpoint)
    
    if is_limited:
        headers = {"Retry-After": str(retry_after)} if retry_after else {}
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=error_message,
            headers=headers
        )
    
    # Record this request
    rate_limiter.record_request(client_id, endpoint)

# Rate limiting statistics endpoint
def get_rate_limit_stats() -> Dict:
    """Get current rate limiting statistics."""
    current_time = time.time()
    stats = {
        "total_tracked_clients": len(rate_limiter.request_history),
        "cleanup_interval_seconds": rate_limiter._cleanup_interval,
        "last_cleanup": datetime.fromtimestamp(rate_limiter._last_cleanup).isoformat(),
        "rate_limits": rate_limiter.rate_limits,
        "active_clients": []
    }
    
    # Add stats for active clients (last hour)
    hour_ago = current_time - 3600
    for (client_id, endpoint), timestamps in rate_limiter.request_history.items():
        recent_requests = [ts for ts in timestamps if ts > hour_ago]
        if recent_requests:
            stats["active_clients"].append({
                "client_id": client_id,
                "endpoint": endpoint,
                "requests_last_hour": len(recent_requests),
                "last_request": datetime.fromtimestamp(max(recent_requests)).isoformat()
            })
    
    # Sort by most recent activity
    stats["active_clients"].sort(key=lambda x: x["last_request"], reverse=True)
    
    return stats