from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, validator
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi_jwt_auth import AuthJWT
from db.database import client_db
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/client",
    tags=["client"],
    responses={404: {"description": "Not found"}},
)

client_db = client_db()

# Android API level constants for modern device support
ANDROID_API_LEVELS = {
    "5": 21,      # Lollipop (min recommended)
    "6": 23,      # Marshmallow
    "7": 24,      # Nougat
    "8": 26,      # Oreo
    "9": 28,      # Pie
    "10": 29,     # Q
    "11": 30,     # R
    "12": 31,     # S
    "13": 33,     # Tiramisu
    "14": 34,     # UpsideDownCake
    "15": 35,     # VanillaIceCream
}

# Min/Max polling interval (milliseconds)
MIN_INTERVAL_MS = 1000      # 1 second minimum (don't spam)
MAX_INTERVAL_MS = 60000     # 60 seconds maximum
DEFAULT_INTERVAL_MS = 3000  # 3 seconds default


class client(BaseModel):
    android_version: str
    device_name: str
    sim_operator: str
    sim_country: str
    interval: int = DEFAULT_INTERVAL_MS
    active: bool = True
    last_online: str = None
    
    # Validators for Android 12+ compatibility
    @validator('android_version')
    def validate_android_version(cls, v):
        """Validate Android version string (supports 5-15)"""
        if not v or len(v) > 2:
            raise ValueError('Invalid Android version')
        # Accept versions 5 through 15
        try:
            version_num = int(v)
            if version_num < 5 or version_num > 15:
                logger.warning(f"Unsupported Android version: {v}")
        except ValueError:
            raise ValueError('Android version must be numeric')
        return v
    
    @validator('device_name')
    def validate_device_name(cls, v):
        """Sanitize device name for all Android versions"""
        if not v or len(v) > 256:
            raise ValueError('Invalid device name')
        # Remove potentially problematic characters
        return v.replace('\0', '').strip()
    
    @validator('interval')
    def validate_interval(cls, v):
        """Enforce minimum interval to prevent API spam (Android 12+ requirement)"""
        if v is None:
            return DEFAULT_INTERVAL_MS
        try:
            interval = int(v)
            if interval < MIN_INTERVAL_MS:
                logger.warning(f"Interval {interval}ms too low, enforcing minimum {MIN_INTERVAL_MS}ms")
                return MIN_INTERVAL_MS
            if interval > MAX_INTERVAL_MS:
                logger.warning(f"Interval {interval}ms too high, capping at maximum {MAX_INTERVAL_MS}ms")
                return MAX_INTERVAL_MS
            return interval
        except (TypeError, ValueError):
            logger.error(f"Invalid interval value: {v}, using default")
            return DEFAULT_INTERVAL_MS
    
    @validator('sim_operator')
    def validate_sim_operator(cls, v):
        """Validate SIM operator string"""
        if v and len(v) > 128:
            raise ValueError('SIM operator name too long')
        return v or "Unknown"
    
    @validator('sim_country')
    def validate_sim_country(cls, v):
        """Validate country code (should be 2-letter ISO code)"""
        if v and len(v) > 2:
            raise ValueError('Country code must be 2 letters')
        return v or "XX"


async def update_lasttime(device_id: str):
    """Update device last online timestamp - used for keep-alive tracking"""
    try:
        client_db.update(
            key=device_id,
            updates={"last_online": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        )
    except Exception as e:
        logger.error(f"Failed to update device {device_id} status: {e}")


@router.post("/add")
async def add_client(client_data: client):
    """
    Register a new Android device.
    Supports Android 5 (API 21) through Android 15 (API 35).
    """
    try:
        # Set initial online timestamp
        client_data.last_online = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Store in database
        user = client_db.put(jsonable_encoder(client_data))
        
        logger.info(
            f"Device registered: {client_data.device_name} "
            f"(Android {client_data.android_version}, "
            f"Interval: {client_data.interval}ms)"
        )
        
        return JSONResponse(
            {
                "success": True,
                "key": user["key"],
                "message": "client added successfully",
                "interval": client_data.interval,  # Echo back validated interval
                "api_level": ANDROID_API_LEVELS.get(client_data.android_version, 0)
            }
        )
    except Exception as e:
        logger.error(f"Error adding client: {e}")
        return JSONResponse(
            {"success": False, "message": f"Failed to register device: {str(e)}"},
            status_code=400
        )


@router.get("/device/{key}")
async def get_client(key: str, Authorize: AuthJWT = Depends()):
    """
    Get device information - requires JWT authentication.
    Includes connection status and recommended settings for Android version.
    """
    Authorize.jwt_required()
    try:
        device = client_db.get(key)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Check if device is considered online (within last 5 minutes)
        last_online = datetime.fromisoformat(device.get("last_online", datetime.now().isoformat()))
        is_online = (datetime.now() - last_online) < timedelta(minutes=5)
        
        return JSONResponse({
            "success": True,
            "client": device,
            "is_online": is_online,
            "last_online_ago": str(datetime.now() - last_online)
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving device {key}: {e}")
        return JSONResponse(
            {"success": False, "message": f"Error: {str(e)}"},
            status_code=500
        )


@router.get("/")
async def get_all_clients(Authorize: AuthJWT = Depends()):
    """
    Get all registered devices - requires JWT authentication.
    Returns devices sorted by last online status.
    """
    Authorize.jwt_required()
    try:
        clients = client_db.fetch().items
        
        # Add online status for each device
        result = []
        for device in clients:
            try:
                last_online = datetime.fromisoformat(device.get("last_online", datetime.now().isoformat()))
                is_online = (datetime.now() - last_online) < timedelta(minutes=5)
                device["is_online"] = is_online
            except:
                device["is_online"] = False
            result.append(device)
        
        # Sort by last online (most recent first)
        result = sorted(
            result,
            key=lambda i: datetime.fromisoformat(i["last_online"]) if i.get("last_online") else datetime.min,
            reverse=True,
        )
        
        return JSONResponse(
            {
                "success": True,
                "clients": result,
                "total": len(result),
                "online_count": sum(1 for c in result if c.get("is_online", False))
            }
        )
    except Exception as e:
        logger.error(f"Error retrieving clients: {e}")
        return JSONResponse(
            {"success": False, "message": f"Error: {str(e)}"},
            status_code=500
        )


@router.post("/keepalive/{device_id}")
async def keepalive(device_id: str):
    """
    Keep-alive endpoint for Android devices.
    Prevents device from being marked as offline.
    This is crucial for Android 12+ background restriction handling.
    """
    try:
        await update_lasttime(device_id)
        return JSONResponse(
            {
                "success": True,
                "message": "Device keep-alive received",
                "server_time": datetime.now().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Keep-alive error for {device_id}: {e}")
        return JSONResponse(
            {"success": False, "message": "Failed to register keep-alive"},
            status_code=500
        )
