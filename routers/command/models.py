from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator


class Coordinate(BaseModel):
    lat: float = Field(..., description="Latitude")
    lng: float = Field(..., description="Longitude")
    accuracy: Optional[float] = 0.0
    altitude: Optional[float] = 0.0
    provider: str = "unknown"
    timestamp: Optional[str] = None

    @validator("accuracy", "altitude", pre=True)
    def coerce_null_to_default(cls, v):
        if v is None:
            return 0.0
        return v


class LocationPayload(BaseModel):
    location: Coordinate

    @validator("location", pre=True)
    def coerce_location(cls, v):
        if isinstance(v, dict):
            if "lat" in v and "lng" in v:
                return v
            if "latitude" in v and "longitude" in v:
                return {"lat": v["latitude"], "lng": v["longitude"],
                        "accuracy": v.get("accuracy", 0.0),
                        "altitude": v.get("altitude", 0.0),
                        "provider": v.get("provider", "unknown")}
        return v


class ContactEntry(BaseModel):
    name: str = ""
    number: str = ""
    email: str = ""


class ContactListPayload(BaseModel):
    contact: Union[List[ContactEntry], Dict[str, Any]]

    @validator("contact", pre=True)
    def normalize_contact(cls, v):
        if isinstance(v, dict):
            items = []
            for key, val in v.items():
                if isinstance(val, dict):
                    items.append({
                        "name": val.get("name", val.get("Name", str(key))),
                        "number": val.get("number", val.get("Number", "")),
                        "email": val.get("email", val.get("Email", "")),
                    })
                else:
                    items.append({"name": str(key), "number": str(val), "email": ""})
            return items
        return v


class AppEntry(BaseModel):
    app_name: str = ""
    package_name: str = ""
    version: str = ""


class AppListPayload(BaseModel):
    installed_apps: List[AppEntry]

    @validator("installed_apps", pre=True)
    def normalize_apps(cls, v):
        if isinstance(v, list):
            result = []
            for item in v:
                if isinstance(item, str):
                    result.append({"app_name": item, "package_name": item, "version": ""})
                elif isinstance(item, dict):
                    name = item.get("app_name", item.get("name", item.get("Name", "")))
                    pkg = item.get("package_name", item.get("package", item.get("Package", "")))
                    result.append({
                        "app_name": name or pkg,
                        "package_name": pkg or name,
                        "version": item.get("version", item.get("Version", "")),
                    })
                else:
                    result.append({"app_name": str(item), "package_name": str(item), "version": ""})
            return result
        return v


class FileEntry(BaseModel):
    name: str = ""
    path: str = ""
    size: Optional[int] = 0
    is_dir: bool = False
    modified: str = ""

    @validator("size", pre=True)
    def coerce_null_size(cls, v):
        if v is None:
            return 0
        return v


class FileListPayload(BaseModel):
    files: List[FileEntry]

    @validator("files", pre=True)
    def normalize_files(cls, v):
        if isinstance(v, list):
            result = []
            for item in v:
                if isinstance(item, str):
                    result.append({"name": item, "path": item, "size": 0, "is_dir": False, "modified": ""})
                elif isinstance(item, dict):
                    result.append({
                        "name": item.get("name", item.get("Name", "")),
                        "path": item.get("path", item.get("Path", item.get("name", item.get("Name", "")))),
                        "size": item.get("size", item.get("Size", 0)),
                        "is_dir": item.get("is_dir", item.get("isDirectory", item.get("IsDir", False))),
                        "modified": item.get("modified", item.get("Modified", item.get("lastModified", ""))),
                    })
                else:
                    result.append({"name": str(item), "path": str(item)})
            return result
        return v


class FileContentPayload(BaseModel):
    filename: str = ""
    content: str = ""


class ServiceEntry(BaseModel):
    name: str = ""
    package: str = ""
    state: str = ""


class ServiceListPayload(BaseModel):
    services: List[ServiceEntry]

    @validator("services", pre=True)
    def normalize_services(cls, v):
        if isinstance(v, list):
            result = []
            for item in v:
                if isinstance(item, str):
                    result.append({"name": item, "package": item, "state": ""})
                elif isinstance(item, dict):
                    result.append({
                        "name": item.get("name", item.get("Name", item.get("service", ""))),
                        "package": item.get("package", item.get("Package", item.get("pkg", ""))),
                        "state": item.get("state", item.get("State", "")),
                    })
                else:
                    result.append({"name": str(item), "package": str(item)})
            return result
        return v


COMMAND_MODEL_MAP = {
    "getlocation": LocationPayload,
    "getcontact": ContactListPayload,
    "getapps": AppListPayload,
    "listfile": FileListPayload,
    "getfile": FileContentPayload,
    "getservices": ServiceListPayload,
}
