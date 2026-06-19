# Mspay Do - Quick Start (5 Minutes)

## Prerequisites

- Firebase project (free tier OK)
- GitHub account for Render deployment
- Python 3.8+

## 1️⃣ Firebase Setup (2 min)

1. Create project: [firebase.google.com](https://firebase.google.com)
2. Create **Realtime Database** (test mode)
3. Enable **Email/Password** auth
4. Download service account key → save as `firebase-key.json`

## 2️⃣ Configure App (1 min)

```bash
# Copy .env template
cp .env.example .env

# Edit .env with your Firebase URL and credentials
# FIREBASE_DATABASE_URL=https://YOUR-PROJECT.firebaseio.com
# FIREBASE_CREDENTIALS_PATH=firebase-key.json
```

## 3️⃣ Deploy Backend (1 min)

Push to GitHub, then on Render:

1. New Web Service → Select your repo
2. Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. Set env vars (copy from `.env.example`)
4. Deploy ✅

You get URL: `https://your-api.onrender.com`

## 4️⃣ Deploy Dashboard (1 min)

```bash
npm install -g firebase-tools
firebase init hosting   # Select your project
# Copy dashboard.html to public/
firebase deploy --only hosting
```

Dashboard live at: `https://your-project.web.app`

## 🎯 Done!

- **API URL** → Configure in Android app
- **Dashboard URL** → Monitor real-time data
- **Firebase Console** → View raw data

## Data Flow

```
Android App
    ↓ (POST /api/data)
Render Python API
    ↓ (Push to Firebase)
Firebase Realtime DB
    ↓ (Real-time listener)
Web Dashboard
    ↓ (Beautiful UI)
Admin Views Live Data
```

---

For detailed setup: See [FIREBASE_SETUP.md](./FIREBASE_SETUP.md)
