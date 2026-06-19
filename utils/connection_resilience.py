"""
Connection Resilience & Retry Logic for Android Compatibility
Ensures the app stays connected across network interruptions and Android 12+ restrictions
"""

import time
import logging
from typing import Callable, Any, Optional
import asyncio

logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuration for retry logic"""
    
    def __init__(
        self,
        max_retries: int = 5,
        initial_delay: float = 1.0,
        max_delay: float = 300.0,  # 5 minutes
        exponential_base: float = 2.0,
        jitter: bool = True,
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter


def exponential_backoff_async(config: Optional[RetryConfig] = None):
    """
    Async decorator for exponential backoff retry logic.
    Supports Android network interruptions and Render sleep mode.
    
    Usage:
        @exponential_backoff_async()
        async def my_function():
            return await some_operation()
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(config.max_retries):
                try:
                    result = await func(*args, **kwargs)
                    if attempt > 0:
                        logger.info(f"✓ {func.__name__} succeeded after {attempt} retries")
                    return result
                except Exception as e:
                    last_exception = e
                    
                    if attempt < config.max_retries - 1:
                        # Calculate backoff delay
                        delay = min(
                            config.initial_delay * (config.exponential_base ** attempt),
                            config.max_delay
                        )
                        
                        # Add jitter to prevent thundering herd
                        if config.jitter:
                            import random
                            delay = delay * (0.5 + random.random())
                        
                        logger.warning(
                            f"⚠️ {func.__name__} attempt {attempt + 1} failed: {str(e)}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"✗ {func.__name__} failed after {config.max_retries} attempts: {str(e)}"
                        )
            
            raise last_exception or Exception(f"{func.__name__} failed after {config.max_retries} retries")
        
        return wrapper
    return decorator


class ConnectionPool:
    """
    Manages device connection states and keep-alive tracking.
    Handles Android 12+ background restrictions.
    """
    
    def __init__(self, timeout_seconds: int = 300):
        """
        timeout_seconds: Time after which device is considered offline (default 5 min)
        """
        self.devices = {}
        self.timeout_seconds = timeout_seconds
        self.last_check = {}
    
    def register_device(self, device_id: str, metadata: dict = None) -> bool:
        """Register a new device"""
        try:
            self.devices[device_id] = {
                "registered_at": time.time(),
                "last_seen": time.time(),
                "metadata": metadata or {},
                "connection_count": 0,
                "failed_attempts": 0,
            }
            logger.info(f"Device registered: {device_id}")
            return True
        except Exception as e:
            logger.error(f"Error registering device {device_id}: {e}")
            return False
    
    def update_device_status(self, device_id: str, online: bool = True) -> bool:
        """Update device keep-alive status"""
        try:
            if device_id not in self.devices:
                self.register_device(device_id)
            
            self.devices[device_id]["last_seen"] = time.time()
            self.devices[device_id]["connection_count"] += 1
            
            if not online:
                self.devices[device_id]["failed_attempts"] += 1
            else:
                self.devices[device_id]["failed_attempts"] = 0
            
            return True
        except Exception as e:
            logger.error(f"Error updating device {device_id}: {e}")
            return False
    
    def is_device_online(self, device_id: str) -> bool:
        """Check if device is considered online"""
        if device_id not in self.devices:
            return False
        
        last_seen = self.devices[device_id]["last_seen"]
        elapsed = time.time() - last_seen
        
        return elapsed < self.timeout_seconds
    
    def get_offline_devices(self) -> list:
        """Get list of devices that haven't checked in"""
        offline = []
        current_time = time.time()
        
        for device_id, info in self.devices.items():
            if current_time - info["last_seen"] > self.timeout_seconds:
                offline.append({
                    "device_id": device_id,
                    "last_seen_seconds_ago": current_time - info["last_seen"],
                    "connection_count": info["connection_count"],
                    "failed_attempts": info["failed_attempts"],
                })
        
        return offline
    
    def get_stats(self) -> dict:
        """Get connection pool statistics"""
        total_devices = len(self.devices)
        online_count = sum(1 for d in self.devices if self.is_device_online(d))
        
        return {
            "total_devices": total_devices,
            "online_devices": online_count,
            "offline_devices": total_devices - online_count,
            "devices": self.devices
        }


# Global connection pool
_connection_pool = None


def get_connection_pool() -> ConnectionPool:
    """Get or create global connection pool"""
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = ConnectionPool(timeout_seconds=300)  # 5 minutes
    return _connection_pool


def heartbeat_monitor(interval_seconds: int = 60):
    """
    Decorator for heartbeat monitoring tasks.
    Runs periodically to check device status.
    """
    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            while True:
                try:
                    await func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Heartbeat monitor error: {e}")
                
                await asyncio.sleep(interval_seconds)
        
        return wrapper
    return decorator


# Android-specific connection constants
ANDROID_CONNECTION_SETTINGS = {
    "5": {
        "api_level": 21,
        "min_interval_ms": 1000,
        "timeout_seconds": 300,
        "description": "Lollipop"
    },
    "6": {
        "api_level": 23,
        "min_interval_ms": 1000,
        "timeout_seconds": 300,
        "description": "Marshmallow - Runtime permissions"
    },
    "7": {
        "api_level": 24,
        "min_interval_ms": 1000,
        "timeout_seconds": 300,
        "description": "Nougat"
    },
    "8": {
        "api_level": 26,
        "min_interval_ms": 1000,
        "timeout_seconds": 300,
        "description": "Oreo - Background restrictions"
    },
    "9": {
        "api_level": 28,
        "min_interval_ms": 1000,
        "timeout_seconds": 300,
        "description": "Pie - Gesture navigation"
    },
    "10": {
        "api_level": 29,
        "min_interval_ms": 1000,
        "timeout_seconds": 300,
        "description": "Q - Scoped storage"
    },
    "11": {
        "api_level": 30,
        "min_interval_ms": 1000,
        "timeout_seconds": 300,
        "description": "R - Power controls"
    },
    "12": {
        "api_level": 31,
        "min_interval_ms": 2000,  # Stricter for Android 12
        "timeout_seconds": 300,
        "description": "S - Background restrictions enforced"
    },
    "13": {
        "api_level": 33,
        "min_interval_ms": 2000,  # Stricter for Android 13
        "timeout_seconds": 300,
        "description": "Tiramisu - Notification runtime permissions"
    },
    "14": {
        "api_level": 34,
        "min_interval_ms": 3000,  # Even stricter for Android 14
        "timeout_seconds": 300,
        "description": "UpsideDownCake - Regional preferences"
    },
    "15": {
        "api_level": 35,
        "min_interval_ms": 3000,  # Stricter for Android 15
        "timeout_seconds": 300,
        "description": "VanillaIceCream - Latest restrictions"
    }
}


def get_android_settings(android_version: str) -> dict:
    """Get recommended connection settings for Android version"""
    return ANDROID_CONNECTION_SETTINGS.get(android_version, ANDROID_CONNECTION_SETTINGS["15"])
