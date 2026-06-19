# Mspay Do
Mspay Do API

## Deployment Options

### Option 1: Firebase + Render (Recommended - Free Tier)

> **New in v4**: Firebase Realtime Database integration to bypass Render's storage limitations and sleep mode!

This setup uses:
- **Render.com** for Python API (runs 24/7, but data not stored locally)
- **Firebase Realtime Database** for persistent data storage
- **Firebase Hosting** for beautiful real-time dashboard

**Benefits:**
- ✅ Unlimited data storage (Firebase free tier)
- ✅ Real-time data visualization
- ✅ API gateway doesn't go to sleep (data persists in Firebase)
- ✅ Beautiful admin dashboard
- ✅ Built-in authentication

**Quick Start:**
1. Create Firebase project (free tier)
2. Deploy Python backend to Render
3. Deploy dashboard to Firebase Hosting

📖 See [FIREBASE_SETUP.md](./FIREBASE_SETUP.md) for detailed instructions  
⚡ See [QUICKSTART.md](./QUICKSTART.md) for 5-minute setup

### Option 2: Legacy Deta Backend

You can host it on [deta.sh](https://deta.sh/)

[![Deploy](https://button.deta.dev/1/svg)](https://go.deta.dev/deploy?repo=https://github.com/ScRiPt1337/MspayDo)

## System Architecture

```
Android Client → Render API → Firebase DB ← Dashboard UI
```

Data flows from the Android app to Render, which immediately forwards it to Firebase. Your dashboard pulls real-time data directly from Firebase, so it works even when Render is sleeping.

## Files Overview

- `main.py` - FastAPI application entry point
- `db/firebase.py` - Firebase Realtime Database integration
- `db/database.py` - Database abstraction layer (Firebase or Deta)
- `routers/` - API routes (client, notification, command, auth)
- `dashboard.html` - Real-time admin dashboard
- `FIREBASE_SETUP.md` - Complete Firebase setup guide
- `QUICKSTART.md` - 5-minute quick start
- `FIREBASE_ENHANCEMENTS.md` - Advanced Firebase features

## Environment Variables

```bash
# Firebase (Primary)
FIREBASE_DATABASE_URL=https://your-project.firebaseio.com
FIREBASE_CREDENTIALS_PATH=firebase-key.json

# Deta (Optional Fallback)
DETA_PROJECT_KEY=your_key

# JWT
JWT_SECRET_KEY=jaihind
```

## API Endpoints

All endpoints available at `https://your-api.onrender.com`:

- `POST /client/add` - Register device
- `GET /client/` - List all devices (auth required)
- `GET /client/device/{key}` - Get device details (auth required)
- `POST /notification/add` - Log notification
- `GET /notification/device/{device_id}` - Get notifications (auth required)
- `POST /command/add` - Send command
- `GET /command/` - List commands (auth required)
- `POST /auth/login` - Authenticate

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn main:app --reload

# API docs available at http://localhost:8000/docs
```

## Dashboard

Access your real-time admin panel at: `https://your-project.web.app`

Features:
- Real-time device status
- Live notification feed
- Command tracking
- Device analytics
- Firebase authentication
