# Firebase Enhancement Examples

This file shows optional enhancements you can add to Mspay Do to leverage Firebase's real-time capabilities.

## 1. Real-Time Push Notifications (Android App)

Update the Android app to listen for Firebase messages when the app is in background:

```python
# In routers/notification/notification.py
# Add this to send Firebase notifications to the Android app

from firebase_admin import messaging
from fastapi import APIRouter

@router.post("/send-to-device/{device_id}")
async def send_notification_to_device(device_id: str, title: str, body: str, Authorize: AuthJWT = Depends()):
    """Send push notification to a specific device via Firebase Cloud Messaging (FCM)"""
    Authorize.jwt_required()
    
    try:
        # This requires the device to register its FCM token with your backend
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            topic=device_id
        )
        response = messaging.send(message)
        return JSONResponse({
            "success": True,
            "message": "Notification sent",
            "message_id": response
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)
```

## 2. Add Health Check Endpoint

Keep Render from sleeping by adding a health check:

```python
# In main.py, add this route

@app.get("/health")
async def health_check():
    """Health check endpoint - call regularly to keep Render awake"""
    return JSONResponse({"status": "healthy", "timestamp": datetime.now().isoformat()})
```

Then set up a cron job (GitHub Actions):

```yaml
# .github/workflows/keep-alive.yml
name: Keep Render Alive
on:
  schedule:
    - cron: '*/15 * * * *'  # Every 15 minutes

jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - name: Ping Render API
        run: curl https://your-api.onrender.com/health
```

## 3. Add Firebase Cloud Functions (Optional Advanced)

Automatically process data with Firebase Cloud Functions:

```javascript
// functions/index.js

const functions = require("firebase-functions");
const admin = require("firebase-admin");

admin.initializeApp();

// Trigger when new notification is added
exports.processNotification = functions.database
    .ref('/notification/{notifId}')
    .onCreate((snapshot, context) => {
        const notification = snapshot.val();
        
        // Example: Send alert if suspicious app detected
        if (notification.Package.includes("banking")) {
            console.log("⚠️ Suspicious app detected:", notification.Package);
            // Send admin alert
        }
        
        return null;
    });

// Trigger when device goes offline
exports.trackDeviceStatus = functions.database
    .ref('/client/{clientId}/last_online')
    .onUpdate((change, context) => {
        const newTime = change.after.val();
        const oldTime = change.before.val();
        
        console.log(`Device ${context.params.clientId} updated: ${oldTime} → ${newTime}`);
        return null;
    });
```

Deploy with:
```bash
cd functions
firebase deploy --only functions
```

## 4. Database Backup Strategy

Back up Firebase data regularly:

```python
# backup_firebase.py

import firebase_admin
from firebase_admin import credentials, db
import json
from datetime import datetime

def backup_database():
    """Backup entire Firebase database to JSON file"""
    ref = db.reference('/')
    data = ref.get().val()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✓ Backup saved to {filename}")

if __name__ == "__main__":
    backup_database()
```

Schedule with cron:
```bash
# Run daily backup
0 2 * * * cd /path/to/mspaydo && python backup_firebase.py
```

## 5. Advanced Dashboard Features

### Real-Time Search

```html
<input type="text" id="searchBox" placeholder="Search notifications...">

<script>
document.getElementById('searchBox').addEventListener('keyup', (e) => {
    const query = e.target.value.toLowerCase();
    const items = document.querySelectorAll('.notification-item');
    
    items.forEach(item => {
        const text = item.textContent.toLowerCase();
        item.style.display = text.includes(query) ? 'block' : 'none';
    });
});
</script>
```

### Export Data to CSV

```javascript
function exportToCSV() {
    const data = Object.entries(notifications).map(([key, notif]) => ({
        'Device ID': notif.device_id,
        'Package': notif.Package,
        'Title': notif.titleText,
        'Body': notif.notificationBodyText,
        'Date': notif.date
    }));
    
    const csv = [
        Object.keys(data[0]).join(','),
        ...data.map(row => Object.values(row).join(','))
    ].join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'notifications.csv';
    a.click();
}
```

### Real-Time Charts (Chart.js)

```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>

<canvas id="notificationChart"></canvas>

<script>
const ctx = document.getElementById('notificationChart').getContext('2d');
const chart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [{
            label: 'Notifications per hour',
            data: [],
            borderColor: '#667eea',
            tension: 0.4
        }]
    }
});

// Update chart on Firebase updates
db.ref('/notification').on('value', snapshot => {
    // Process and update chart data
});
</script>
```

## 6. Multi-Device Command Broadcasting

Send commands to all connected devices:

```python
# In routers/command/command.py

@router.post("/broadcast")
async def broadcast_command(command: str, Authorize: AuthJWT = Depends()):
    """Send command to all connected devices"""
    Authorize.jwt_required()
    
    cmd_db = command_db()
    all_clients = client_db().fetch().items
    
    for client in all_clients:
        cmd_db.put({
            "device_id": client["key"],
            "command": command,
            "timestamp": datetime.now().isoformat()
        })
    
    return JSONResponse({
        "success": True,
        "devices_targeted": len(all_clients)
    })
```

## 7. Analytics Dashboard

Track usage patterns:

```javascript
// In dashboard.html

function generateAnalytics() {
    const deviceCounts = {};
    const appCounts = {};
    
    Object.values(notifications).forEach(notif => {
        deviceCounts[notif.device_id] = (deviceCounts[notif.device_id] || 0) + 1;
        appCounts[notif.Package] = (appCounts[notif.Package] || 0) + 1;
    });
    
    console.log("Notifications by device:", deviceCounts);
    console.log("Most active apps:", appCounts);
}
```

---

## Security Reminders

1. **Never** commit `firebase-key.json` to git
2. **Always** use environment variables for secrets
3. **Enable** proper Firebase security rules in production
4. **Rotate** service account keys periodically
5. **Monitor** Firebase usage to avoid exceeding free tier

---

See main [FIREBASE_SETUP.md](./FIREBASE_SETUP.md) for complete setup guide.
