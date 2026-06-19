# Mspay Do Firebase Integration Guide

This guide walks you through setting up Mspay Do to use Firebase Realtime Database instead of Render's limited storage, along with a real-time dashboard on Firebase Hosting.

## System Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│  Android Client │         │  Python Backend  │         │  Firebase       │
│   (Mspay Do)    │────────▶│  (Render.com)    │────────▶│  Realtime DB    │
│                 │  Every  │                  │         │                 │
│  Sends Data     │  Second │  Forwards to     │  Store  │  Persistent     │
│                 │         │  Firebase        │  Data   │  Storage        │
└─────────────────┘         └──────────────────┘         └─────────────────┘
                                                                    │
                                                                    │
                                                                    ▼
                                                          ┌─────────────────┐
                                                          │  Firebase       │
                                                          │  Hosting        │
                                                          │  Dashboard      │
                                                          │                 │
                                                          │  Real-Time UI   │
                                                          │  + Auth         │
                                                          └─────────────────┘
```

## Step 1: Set Up Firebase Project

### 1.1 Create a Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click **+ Add project**
3. Enter project name (e.g., "mspaydo-admin")
4. Proceed through the setup wizard

### 1.2 Enable Realtime Database

1. In the Firebase console, go to **Realtime Database** (under Build > Realtime Database)
2. Click **Create Database**
3. Select region (closest to your location)
4. Choose **Start in test mode** (for development; set proper rules later)
5. Click **Enable**

### 1.3 Set Up Authentication

1. Go to **Authentication** (under Build > Authentication)
2. Click **Get Started**
3. Enable **Email/Password** sign-in method
4. (Optional) Create a test user: admin@example.com / password123

### 1.4 Get Service Account Credentials

1. Go to **Project Settings** (gear icon, top-right)
2. Select **Service Accounts** tab
3. Click **Generate New Private Key**
4. Save the `.json` file as `firebase-key.json`

**⚠️ Keep this file secure! Never commit it to git.**

### 1.5 Get Firebase Web Config

1. In Project Settings, go to **Your apps**
2. Click the `</>` icon to create a web app
3. Copy the Firebase configuration object (you'll need this for the dashboard)

## Step 2: Configure Python Backend

### 2.1 Set Environment Variables

Create a `.env` file in the project root:

```bash
# Firebase Configuration
FIREBASE_DATABASE_URL=https://your-project-name.firebaseio.com
FIREBASE_CREDENTIALS_PATH=firebase-key.json

# (Optional) If using Deta as fallback
DETA_PROJECT_KEY=your_deta_key

# JWT Secret
JWT_SECRET_KEY=jaihind
```

### 2.2 Place Firebase Key File

Place your `firebase-key.json` file in the project root directory.

### 2.3 Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `fastapi` - Web framework
- `firebase-admin` - Firebase SDK
- `python-multipart` - Request handling
- `fastapi-jwt-auth` - JWT authentication
- `python-dotenv` - Environment variables

### 2.4 Test Firebase Connection

```bash
python -c "
from db.firebase import init_firebase
try:
    init_firebase()
    print('✓ Firebase connection successful!')
except Exception as e:
    print(f'✗ Error: {e}')
"
```

## Step 3: Deploy Python Backend to Render

### 3.1 Create Render Account

1. Go to [Render.com](https://render.com/)
2. Sign up with GitHub or email

### 3.2 Deploy Flask App

1. Push your code to GitHub (with `.gitignore` excluding `.env` and `firebase-key.json`)
2. In Render dashboard, click **New** → **Web Service**
3. Connect your GitHub repository
4. Configure:
   - **Name**: mspaydo-api
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Free

### 3.3 Set Environment Variables on Render

1. Go to **Environment** tab
2. Add environment variables:
   - `FIREBASE_DATABASE_URL`: Your Firebase database URL
   - `FIREBASE_CREDENTIALS_JSON`: Paste the entire contents of `firebase-key.json` (as a JSON string)

   **OR**

   - Upload `firebase-key.json` via Render's file upload or use the JSON string method

### 3.4 Deploy

Click **Deploy** and wait for the service to be live.

You'll get a URL like: `https://mspaydo-api.onrender.com`

Give this URL to the Android app to report data to.

## Step 4: Update Dashboard HTML

### 4.1 Edit `dashboard.html`

Open `dashboard.html` and update the Firebase config:

```javascript
const firebaseConfig = {
    apiKey: "YOUR_API_KEY",
    authDomain: "your-project.firebaseapp.com",
    databaseURL: "https://your-project.firebaseio.com",
    projectId: "your-project",
    storageBucket: "your-project.appspot.com",
    messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
    appId: "YOUR_APP_ID"
};
```

Get these values from Firebase Console → Project Settings → Your apps → Web config.

### 4.2 Enable Firebase Hosting

In Firebase Console:
1. Go to **Hosting** (under Build)
2. Click **Get Started**
3. Install Firebase CLI: `npm install -g firebase-tools`
4. Initialize in your project: `firebase init hosting`
   - Select your project
   - Set public directory to `./` or create a public folder
5. Copy `dashboard.html` to the public folder

### 4.3 Deploy Dashboard

```bash
firebase deploy --only hosting
```

Your dashboard is now live at: `https://your-project.web.app`

## Step 5: Set Up Firebase Security Rules

### 5.1 Database Rules

In Firebase Console → Realtime Database → Rules, replace with:

```json
{
  "rules": {
    "client": {
      ".read": "auth != null",
      ".write": true
    },
    "notification": {
      ".read": "auth != null",
      ".write": true
    },
    "command": {
      ".read": "auth != null",
      ".write": "auth != null"
    },
    "auth": {
      ".read": "auth != null",
      ".write": "auth != null"
    }
  }
}
```

### 5.2 Hosting Rules (Firebase Hosting)

1. Go to **Hosting** → **Domains**
2. Set up custom domain or use the default `.web.app` domain

## Step 6: Testing

### 6.1 Test API Endpoint

```bash
curl -X POST http://localhost:5000/client/add \
  -H "Content-Type: application/json" \
  -d '{
    "device_name": "Test Phone",
    "android_version": "13",
    "sim_operator": "Verizon",
    "sim_country": "US"
  }'
```

Response should include a key and status: `"success": true`

### 6.2 Verify Firebase Storage

1. Open Firebase Console → Realtime Database
2. You should see data under `/client`

### 6.3 Test Dashboard

1. Open `https://your-project.web.app`
2. Sign in with your Firebase auth credentials
3. You should see real-time device data

## Troubleshooting

### Firebase Connection Error

**Error**: `Error initializing Firebase: Cannot read property 'databaseURL' of undefined`

**Fix**: Ensure `FIREBASE_DATABASE_URL` and `FIREBASE_CREDENTIALS_JSON` are properly set.

### Dashboard Shows No Data

1. Check Firebase authentication is enabled
2. Verify database rules allow read access to authenticated users
3. Check browser console (F12) for errors
4. Ensure data was actually written to Firebase

### Render Service Keeps Sleeping

This is **intentional** — Render's free tier spins down after 15 minutes of inactivity. But your data persists in Firebase!

**Solution**: Set up a simple ping service to keep Render awake:

```bash
# Add to cron job or GitHub Actions
curl https://mspaydo-api.onrender.com/health
```

### File Upload Issues

If using `tear_drive()`, it requires Deta backend. For Firebase-only setup, skip file uploads.

## Environment Variables Summary

```bash
# Firebase (REQUIRED)
FIREBASE_DATABASE_URL=https://your-project.firebaseio.com
FIREBASE_CREDENTIALS_PATH=firebase-key.json
# OR use JSON string:
FIREBASE_CREDENTIALS_JSON={"type":"service_account",...}

# Deta (Optional fallback)
DETA_PROJECT_KEY=your_key

# JWT (Optional, defaults to "jaihind")
JWT_SECRET_KEY=your_secret
```

## API Endpoints

All endpoints are available at your Render URL:

### Client Endpoints

- `POST /client/add` - Register new device
- `GET /client/device/{key}` - Get device info (requires auth)
- `GET /client/` - Get all devices (requires auth)

### Notification Endpoints

- `POST /notification/add` - Record notification
- `GET /notification/device/{device_name}` - Get notifications (requires auth)

### Command Endpoints

- `POST /command/add` - Send command
- `GET /command/` - Get all commands (requires auth)

### Auth Endpoints

- `POST /auth/login` - Authenticate

## Next Steps

1. **Modify Android App**: Update TearDroid to send data to your Render endpoint
2. **Test End-to-End**: Send test data from the app, verify it appears in the dashboard
3. **Set Production Rules**: Once stable, replace test mode with proper Firebase security rules
4. **Monitor & Scale**: Use Firebase analytics and alerts to track performance

---

**Version**: TearDroid v4 + Firebase  
**Last Updated**: June 2026  
**Status**: Production Ready
