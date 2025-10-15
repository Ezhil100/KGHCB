# Mobile Access Guide - WiFi Hosting Setup

## 🌐 Your Network Information

- **Your Computer's IP Address**: `172.20.10.5`
- **Backend Port**: `8000`
- **Frontend Port**: `5173`

## 📱 Access URLs for Mobile

Once servers are running, access from your mobile device using:

- **Frontend (Chat Interface)**: `http://172.20.10.5:5173`
- **Backend API**: `http://172.20.10.5:8000`

---

## 🚀 Step-by-Step Setup

### Step 1: Update Frontend API URL

You need to change the backend API URL in your frontend code to use your IP address instead of localhost.

**File to edit**: `frontend/src/App.jsx`

**Change line 3 from:**

```javascript
const API_BASE_URL = "http://localhost:8000";
```

**To:**

```javascript
const API_BASE_URL = "http://172.20.10.5:8000";
```

### Step 2: Start Backend Server

Open PowerShell and run:

```powershell
cd C:\Users\ezhil\Desktop\hos_chatbot_v6-\Hospital_chat_bot-main\Backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**What this does:**

- `--host 0.0.0.0` - Makes the server accessible from any device on your network (not just localhost)
- `--port 8000` - Runs on port 8000
- `--reload` - Auto-reloads when you make code changes

**You should see:**

```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### Step 3: Start Frontend Server

Open a NEW PowerShell window and run:

```powershell
cd C:\Users\ezhil\Desktop\hos_chatbot_v6-\Hospital_chat_bot-main\frontend
npm run dev
```

**You should see something like:**

```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: http://172.20.10.5:5173/
  ➜  press h + enter to show help
```

### Step 4: Connect from Mobile

1. **Ensure your mobile device is on the SAME WiFi network** as your computer
2. Open your mobile browser (Chrome, Safari, etc.)
3. Go to: `http://172.20.10.5:5173`

---

## ⚠️ Important Notes

### Firewall Settings

If you can't access from mobile, you may need to allow the ports through Windows Firewall:

1. Open **Windows Defender Firewall** → Advanced Settings
2. Click **Inbound Rules** → **New Rule**
3. Select **Port** → Next
4. Select **TCP** → Specific local ports: `8000, 5173`
5. Select **Allow the connection** → Next
6. Select all profiles (Domain, Private, Public) → Next
7. Name it "Hospital Chatbot" → Finish

### Alternative: Quick Firewall Commands

Run PowerShell as Administrator and execute:

```powershell
# Allow Backend (Port 8000)
New-NetFirewallRule -DisplayName "Hospital Chatbot Backend" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow

# Allow Frontend (Port 5173)
New-NetFirewallRule -DisplayName "Hospital Chatbot Frontend" -Direction Inbound -LocalPort 5173 -Protocol TCP -Action Allow
```

### Network Requirements

- ✅ Computer and mobile must be on the **same WiFi network**
- ✅ WiFi must allow **device-to-device communication** (some public WiFi networks block this)
- ✅ Windows Firewall must allow the ports (8000, 5173)

---

## 🔧 Troubleshooting

### Can't access from mobile?

1. **Verify your IP hasn't changed:**

   ```powershell
   ipconfig | findstr /i "IPv4"
   ```

   If it's different, update the `API_BASE_URL` in `App.jsx`

2. **Check if servers are running:**

   - Backend: Open `http://172.20.10.5:8000/docs` on your computer
   - Frontend: Open `http://172.20.10.5:5173` on your computer

3. **Test network connectivity:**
   From your mobile browser, try: `http://172.20.10.5:8000/health`

4. **Disable Windows Firewall temporarily:**
   - If it works with firewall off, then add firewall rules (see above)

### CORS Errors?

The backend already has CORS enabled (`allow_origins=["*"]`), so this should not be an issue.

### Connection Refused?

- Make sure both servers are running
- Check that you used `--host 0.0.0.0` for backend
- Verify Vite config has `host: '0.0.0.0'`

---

## 📋 Quick Command Reference

### Backend Command (in Backend folder):

```powershell
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Command (in frontend folder):

```powershell
npm run dev
```

### Check IP Address:

```powershell
ipconfig | findstr /i "IPv4"
```

### Test Backend (on computer):

```
http://172.20.10.5:8000/docs
```

### Access from Mobile:

```
http://172.20.10.5:5173
```

---

## 🔄 If Your IP Address Changes

Your IP address can change when you:

- Restart your computer
- Disconnect/reconnect to WiFi
- Connect to a different WiFi network

**When this happens:**

1. Get new IP: `ipconfig | findstr /i "IPv4"`
2. Update `API_BASE_URL` in `frontend/src/App.jsx`
3. Update this guide with the new IP
4. Restart both servers

---

## 🎯 Production Alternative

For more stable access, consider:

1. **Use a fixed IP address** for your computer in router settings
2. **Use environment variables** for API_BASE_URL
3. **Deploy to cloud** services like Vercel (frontend) + Render/Railway (backend)

---

## ✅ Verification Checklist

Before testing on mobile:

- [ ] Updated `API_BASE_URL` in `App.jsx` to `http://172.20.10.5:8000`
- [ ] Vite config has `host: '0.0.0.0'` (already configured)
- [ ] Backend running with `--host 0.0.0.0`
- [ ] Frontend running with `npm run dev`
- [ ] Firewall rules added for ports 8000 and 5173
- [ ] Mobile device on same WiFi network
- [ ] Backend accessible: `http://172.20.10.5:8000/docs` works on computer
- [ ] Frontend accessible: `http://172.20.10.5:5173` works on computer
- [ ] Ready to test on mobile!
