# Mspay Do Firebase Deployment Checklist

Use this checklist to ensure all components are properly configured before going live.

## Phase 1: Firebase Setup

- [ ] Created Firebase project at [console.firebase.google.com](https://console.firebase.google.com)
- [ ] Realtime Database created and initialized in test mode
- [ ] Firebase Authentication enabled (Email/Password method)
- [ ] Downloaded service account private key (`firebase-key.json`)
- [ ] Saved Firebase config to a safe location
- [ ] Created test user in Firebase Auth (if needed)
- [ ] Database URL copied from Project Settings

**Firebase URL Format**: `https://your-project-name.firebaseio.com`

**Location of Service Key**: `firebase-key.json` in project root

---

## Phase 2: Python Backend Configuration

- [ ] Cloned repository: `git clone [repo-url]`
- [ ] Installed dependencies: `pip install -r requirements.txt`
- [ ] Created `.env` file from `.env.example` template
- [ ] Added `FIREBASE_DATABASE_URL` to `.env`
- [ ] Added `FIREBASE_CREDENTIALS_PATH` or `FIREBASE_CREDENTIALS_JSON` to `.env`
- [ ] Placed `firebase-key.json` in project root
- [ ] Tested Firebase connection: `python -c "from db.firebase import init_firebase; init_firebase()"`

**Expected Output**: No errors, or "✓ Firebase connection successful!"

---

## Phase 3: Local Testing

- [ ] Started development server: `uvicorn main:app --reload`
- [ ] Accessed API docs at `http://localhost:8000/docs`
- [ ] Tested health endpoint: `curl http://localhost:8000/health`
- [ ] Made test POST to `/client/add` endpoint
- [ ] Verified data appears in Firebase Console → Realtime Database
- [ ] Confirmed database structure `/client` → `{device_key}` → device data

**Test Request Example**:
```bash
curl -X POST http://localhost:8000/client/add \
  -H "Content-Type: application/json" \
  -d '{"device_name":"Test","android_version":"13","sim_operator":"Test","sim_country":"US"}'
```

---

## Phase 4: Render Deployment

- [ ] Code pushed to GitHub (without `.env` and `firebase-key.json`)
- [ ] Verified `.gitignore` excludes sensitive files
- [ ] Created Render account at [render.com](https://render.com)
- [ ] Created new Web Service connected to GitHub repo
- [ ] Set environment variables on Render:
  - [ ] `FIREBASE_DATABASE_URL`
  - [ ] `FIREBASE_CREDENTIALS_JSON` (or uploaded firebase-key.json)
  - [ ] `JWT_SECRET_KEY` (if changed from default)
- [ ] Build command: `pip install -r requirements.txt`
- [ ] Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- [ ] Deployed successfully (status shows "Live" in green)
- [ ] Render URL copied (e.g., `https://mspaydo-api.onrender.com`)

**Test Render Deployment**:
```bash
curl https://your-render-url.onrender.com/health
```

Expected response: `{"status":"healthy","timestamp":"2024-..."}`

---

## Phase 5: Dashboard Configuration

- [ ] Obtained Firebase Web Config from Project Settings → Your apps
- [ ] Updated `dashboard.html` with Firebase config:
  - [ ] `apiKey`
  - [ ] `authDomain`
  - [ ] `databaseURL`
  - [ ] `projectId`
  - [ ] `storageBucket`
  - [ ] `messagingSenderId`
  - [ ] `appId`
- [ ] Verified Firebase config is correct in `dashboard.html`
- [ ] Created test Firebase user for dashboard access

**Location**: Search for `const firebaseConfig = {` in `dashboard.html`

---

## Phase 6: Firebase Hosting Deployment

- [ ] Installed Firebase CLI: `npm install -g firebase-tools`
- [ ] Logged in: `firebase login`
- [ ] Initialized hosting: `firebase init hosting` → Selected your project
- [ ] Copied `dashboard.html` to `public/` directory (or configured path)
- [ ] Deployed: `firebase deploy --only hosting`
- [ ] Dashboard URL obtained (e.g., `https://your-project.web.app`)

**Test Dashboard**:
1. Open `https://your-project.web.app` in browser
2. Sign in with Firebase auth credentials
3. Dashboard should display (loading animation briefly)
4. Stats should show 0 devices initially

---

## Phase 7: Firebase Security Rules

- [ ] Updated Realtime Database security rules
- [ ] Rules allow authenticated reads to `/client`, `/notification`, `/command`
- [ ] Rules allow writes to `/notification` and `/client` (for app to register)
- [ ] Rules restrict `/auth` and `/command` to authenticated users only

**Check Rules**: Firebase Console → Realtime Database → Rules tab

---

## Phase 8: End-to-End Testing

- [ ] Sent test data to Render API: `curl -X POST [render-url]/client/add ...`
- [ ] Verified data appears in Firebase Console
- [ ] Opened dashboard and confirmed real-time update (data visible in UI)
- [ ] Created test account in Firebase Auth
- [ ] Logged into dashboard with test account
- [ ] Dashboard displays connected device(s)
- [ ] Simulated multiple requests and verified real-time updates on dashboard

---

## Phase 9: Production Hardening

- [ ] Updated JWT secret in `.env` (changed from default "jaihind")
- [ ] Enabled proper Firebase security rules (not test mode)
- [ ] Set up database backup strategy
- [ ] Configured Firebase monitoring/alerts (optional)
- [ ] Created separate Firebase projects for dev/prod (recommended)
- [ ] Rotated service account keys periodically (security best practice)
- [ ] Enabled API key restrictions in Firebase (limit to your domains)

---

## Phase 10: Keep-Alive & Monitoring

- [ ] Set up GitHub Actions cron to ping `/health` every 15 minutes
- [ ] Configured Firebase usage alerts
- [ ] Set up log monitoring (Firebase Console → Logs)
- [ ] Created documentation for team on dashboard usage
- [ ] Tested recovery if Render goes down (data should persist in Firebase)

---

## Troubleshooting

### Firebase Connection Failed
- [ ] Check `.env` file has correct `FIREBASE_DATABASE_URL`
- [ ] Verify `firebase-key.json` exists and is readable
- [ ] Confirm file is valid JSON
- [ ] Test: `python -c "import json; json.load(open('firebase-key.json'))"`

### Dashboard Shows No Data
- [ ] Verify you're logged into Firebase Auth
- [ ] Check browser console for JavaScript errors (F12)
- [ ] Confirm data actually exists in Firebase Console
- [ ] Verify Firebase config in `dashboard.html` matches your project
- [ ] Check Firebase Realtime Database security rules

### Render API Returns 500 Error
- [ ] Check Render logs for Python exceptions
- [ ] Verify all environment variables are set on Render
- [ ] Test locally: `uvicorn main:app --reload`
- [ ] Ensure `requirements.txt` includes all dependencies

### Dashboard Won't Authenticate
- [ ] Verify Firebase Auth is enabled in Firebase Console
- [ ] Check test user exists and email/password are correct
- [ ] Verify Firebase auth is included in `dashboard.html`
- [ ] Check browser console for auth errors

---

## Quick Verification Script

```bash
#!/bin/bash
echo "🔍 TearDroid Firebase Verification"
echo ""

echo "1️⃣  Checking Firebase connection..."
python -c "
from db.firebase import init_firebase
try:
    init_firebase()
    print('   ✓ Firebase connected')
except Exception as e:
    print(f'   ✗ Firebase error: {e}')
" || echo "   ✗ Python test failed"

echo ""
echo "2️⃣  Testing local API..."
curl -s http://localhost:8000/health -I | head -1 || echo "   ✗ API not running"

echo ""
echo "3️⃣  Testing Render deployment..."
read -p "   Enter Render URL (e.g., https://your-api.onrender.com): " RENDER_URL
curl -s $RENDER_URL/health | grep -q "healthy" && echo "   ✓ Render is up" || echo "   ✗ Render not responding"

echo ""
echo "4️⃣  Checking environment variables..."
[ -f ".env" ] && echo "   ✓ .env file exists" || echo "   ✗ .env file missing"
grep -q "FIREBASE_DATABASE_URL" .env && echo "   ✓ Firebase URL configured" || echo "   ✗ Firebase URL missing"

echo ""
echo "✅ Verification complete!"
```

---

## Final Checklist Before Launch

- [ ] All 10 phases completed
- [ ] End-to-end test successful
- [ ] Documentation updated for team
- [ ] Backup strategy in place
- [ ] Monitoring configured
- [ ] Team trained on dashboard usage
- [ ] Production security rules deployed
- [ ] Incident response plan created

---

**Status**: 🔴 Not Started | 🟡 In Progress | 🟢 Complete

Set status to **🟢 Complete** once all phases are verified.

---

**Deployment Date**: _______________  
**Deployed By**: _______________  
**Verified By**: _______________  

See [FIREBASE_SETUP.md](./FIREBASE_SETUP.md) for detailed instructions.
