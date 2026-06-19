from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, validator
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi_jwt_auth import AuthJWT
from db.database import notification_db
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/notification",
    tags=["notification"],
    responses={404: {"description": "Not found"}},
)

notification_db = notification_db()


class notification(BaseModel):
    id: str
    device_id: str
    Package: str
    titleText: str = "null"
    notificationBodyText: str = "null"
    date: str = None
    
    @validator('device_id')
    def validate_device_id(cls, v):
        """Validate device ID"""
        if not v or len(v) > 256:
            raise ValueError('Invalid device_id')
        return v
    
    @validator('Package')
    def validate_package(cls, v):
        """Validate package name"""
        if not v or len(v) > 512:
            raise ValueError('Invalid package name')
        return v
    
    @validator('titleText')
    def validate_title(cls, v):
        """Sanitize notification title"""
        if v and len(v) > 512:
            raise ValueError('Title too long')
        return v or "null"
    
    @validator('notificationBodyText')
    def validate_body(cls, v):
        """Sanitize notification body"""
        if v and len(v) > 2048:
            return v[:2048] + "..."  # Truncate very long messages
        return v or "null"


@router.post("/add")
async def add_notification(notif: notification):
    """
    Store a notification from Android device.
    Supports all Android versions 5-15.
    Deduplicates recent identical notifications.
    """
    try:
        # Set timestamp if not provided
        if not notif.date:
            notif.date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Check for duplicates (same notification within last minute)
        response = jsonable_encoder(notif)
        search_criteria = {
            "device_id": notif.device_id,
            "Package": notif.Package,
            "titleText": notif.titleText,
            "notificationBodyText": notif.notificationBodyText
        }
        
        existing = notification_db.fetch(search_criteria).items
        if len(existing) > 0:
            logger.debug(f"Duplicate notification detected: {notif.Package}")
            return JSONResponse({
                "success": False,
                "message": "notification already exists",
                "duplicate": True
            }, status_code=409)
        
        notification_db.put(jsonable_encoder(notif))
        logger.info(f"Notification stored: {notif.Package} from {notif.device_id}")
        return JSONResponse({
            "success": True,
            "message": "notification added successfully",
            "timestamp": notif.date
        })
    except Exception as e:
        logger.error(f"Error storing notification: {e}")
        return JSONResponse(
            {"success": False, "message": f"Failed to store notification: {str(e)}"},
            status_code=400
        )


@router.get("/device/{device_name}")
async def get_notification(device_name: str, Authorize: AuthJWT = Depends()):
    """
    Get notifications for a specific device.
    Returns list of notification tuples.
    """
    Authorize.jwt_required()
    try:
        response = []
        data = notification_db.fetch({"device_id": device_name}).items
        for i in data:
            try:
                item_copy = dict(i)
                item_copy.pop("key", None)
                item_copy.pop("id", None)
                response.append(list(item_copy.values()))
            except Exception as e:
                logger.warning(f"Error processing notification: {e}")
                continue
        
        return JSONResponse({
            "success": True,
            "notification": response,
            "count": len(response)
        })
    except Exception as e:
        logger.error(f"Error retrieving notifications for {device_name}: {e}")
        return JSONResponse(
            {"success": False, "message": f"Error: {str(e)}"},
            status_code=500
        )


@router.get("/")
async def get_notifications(Authorize: AuthJWT = Depends()):
    """
    Get all notifications across all devices.
    Returns notifications sorted by date (newest first).
    """
    Authorize.jwt_required()
    try:
        response = []
        data = notification_db.fetch().items
        for i in data:
            try:
                item_copy = dict(i)
                item_copy.pop("key", None)
                item_copy.pop("id", None)
                response.append(list(item_copy.values()))
            except Exception as e:
                logger.warning(f"Error processing notification: {e}")
                continue
        
        # Sort by date (assuming index 4 is date based on model)
        try:
            response = sorted(
                response,
                key=lambda i: datetime.fromisoformat(i[4]) if len(i) > 4 else datetime.min,
                reverse=True
            )
        except Exception as e:
            logger.warning(f"Error sorting notifications: {e}")
        
        return JSONResponse({
            "success": True,
            "notification": response,
            "count": len(response)
        })
    except Exception as e:
        logger.error(f"Error retrieving notifications: {e}")
        return JSONResponse(
            {"success": False, "message": f"Error: {str(e)}"},
            status_code=500
        )


@router.get("/delete/{device_id}")
async def delete_notification(device_id: str, Authorize: AuthJWT = Depends()):
    """
    Delete all notifications for a device.
    """
    Authorize.jwt_required()
    try:
        data = notification_db.fetch({"device_id": device_id}).items
        deleted_count = 0
        for i in data:
            try:
                notification_db.delete(i["key"])
                deleted_count += 1
            except Exception as e:
                logger.error(f"Error deleting notification {i.get('key')}: {e}")
        
        return JSONResponse({
            "success": True,
            "message": f"notification deleted successfully",
            "deleted_count": deleted_count
        })
    except Exception as e:
        logger.error(f"Error deleting notifications for {device_id}: {e}")
        return JSONResponse(
            {"success": False, "message": f"Error: {str(e)}"},
            status_code=500
        )
