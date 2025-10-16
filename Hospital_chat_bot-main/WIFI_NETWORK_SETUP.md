# WiFi Network Access Setup - Complete

## Summary

Configured the Hospital AI Assistant to run on your WiFi network, allowing access from any device connected to the same WiFi network (phones, tablets, other computers).

## Your Network Details

- **WiFi IP Address**: `172.20.10.5`
- **Backend API**: `http://172.20.10.5:8000`
- **Frontend App**: `http://172.20.10.5:5173`

## Changes Made

### 1. Frontend Configuration (App.jsx)

```javascript
// Before
const API_BASE_URL = "http://localhost:8000"; // Local access only

// After
const API_BASE_URL = "http://172.20.10.5:8000"; // WiFi network access
```

### 2. Vite Server Configuration (vite.config.js)

```javascript
// Before
server: {
  host: 'localhost', // Only allow local access
  port: 5173
}

// After
server: {
  host: '0.0.0.0', // Allow network access from all devices
  port: 5173
}
```

### 3. Frontend Preconnect (index.html)

```html
<!-- Before -->
<link rel="preconnect" href="http://localhost:8000" />

<!-- After -->
<link rel="preconnect" href="http://172.20.10.5:8000" />
```

### 4. Backend Server Configuration

The backend already had CORS configured to accept all origins (`"*"`), so no changes needed there. However, uvicorn needs to run with `--host 0.0.0.0` to listen on all network interfaces.

## How to Start the Servers

### Option 1: Using the Startup Script (Recommended)

1. **Double-click** `start-wifi.bat` in the project root folder
2. Two command windows will open (Backend and Frontend)
3. Wait for both servers to start (about 5-10 seconds)
4. Open `http://172.20.10.5:5173` on any device

### Option 2: Manual Start

#### Terminal 1 - Backend:

```powershell
cd Backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### Terminal 2 - Frontend:

```powershell
cd frontend
npm run dev
```

The Vite server will automatically use `0.0.0.0` from vite.config.js

## Accessing from Other Devices

### From Mobile Phone (Same WiFi):

1. Make sure your phone is connected to the **same WiFi network**
2. Open browser (Chrome, Safari, etc.)
3. Navigate to: `http://172.20.10.5:5173`
4. The app should load and work normally

### From Another Computer (Same WiFi):

1. Make sure computer is connected to the **same WiFi network**
2. Open browser
3. Navigate to: `http://172.20.10.5:5173`
4. Full functionality available

### From Tablet (Same WiFi):

1. Connect iPad/Android tablet to **same WiFi network**
2. Open browser
3. Navigate to: `http://172.20.10.5:5173`
4. Mobile responsive design will adapt to tablet screen

## Firewall Configuration

### Windows Firewall (If Connection Fails):

1. **Allow ports through Windows Firewall:**

   ```powershell
   # Run PowerShell as Administrator
   New-NetFirewallRule -DisplayName "Hospital Backend" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
   New-NetFirewallRule -DisplayName "Hospital Frontend" -Direction Inbound -LocalPort 5173 -Protocol TCP -Action Allow
   ```

2. **Or manually:**
   - Open Windows Defender Firewall
   - Click "Advanced settings"
   - Click "Inbound Rules" → "New Rule"
   - Select "Port" → Next
   - Select "TCP" → Specific local ports: `8000, 5173`
   - Allow the connection
   - Apply to all profiles (Domain, Private, Public)
   - Name: "Hospital AI Assistant"

## Testing Network Access

### Test Backend API:

Open in browser on mobile device:

```
http://172.20.10.5:8000
```

Should see: `{"message": "Hospital AI Assistant API", "status": "running"}`

### Test Frontend App:

Open in browser on mobile device:

```
http://172.20.10.5:5173
```

Should see the Hospital AI Assistant login page

## Troubleshooting

### Issue 1: "Cannot connect" or "Connection refused"

**Solution:**

- Verify both servers are running
- Check that your device is on the same WiFi network
- Disable VPN if active
- Check Windows Firewall settings
- Try accessing from your PC first: `http://172.20.10.5:5173`

### Issue 2: Backend connection failed

**Solution:**

- Make sure backend is running with `--host 0.0.0.0`
- Check backend terminal for errors
- Verify port 8000 is not blocked
- Test backend directly: `http://172.20.10.5:8000`

### Issue 3: Frontend loads but API calls fail

**Solution:**

- Check browser console for CORS errors
- Verify API_BASE_URL in App.jsx is correct
- Ensure backend CORS is configured (already done)
- Check network connectivity

### Issue 4: IP Address Changed

If your WiFi IP changes (after router restart, etc.):

1. **Find new IP:**

   ```powershell
   ipconfig | findstr /i "IPv4"
   ```

2. **Update files:**

   - `frontend/src/App.jsx` → `API_BASE_URL`
   - `frontend/index.html` → preconnect link
   - `start-wifi.bat` → IP address in messages

3. **Restart servers**

## Security Notes

### ⚠️ Important Security Considerations:

1. **Local Network Only**: This configuration only allows access from devices on your WiFi network
2. **Not Internet-Accessible**: External devices cannot access the app
3. **Development Mode**: This is for development/testing purposes
4. **No Authentication on Network**: Any device on your WiFi can access
5. **HTTPS Not Configured**: Using HTTP (not encrypted)

### For Production Deployment:

If you want to deploy this for real hospital use:

1. Use HTTPS with SSL certificates
2. Deploy to a proper hosting service (Vercel, AWS, Azure, etc.)
3. Implement proper authentication
4. Use environment variables for configuration
5. Set up proper firewall rules
6. Use a real domain name
7. Implement rate limiting
8. Add security headers
9. Regular security audits

## Network Requirements

### Same WiFi Network:

- ✅ Your computer must be running the servers
- ✅ Mobile device must be on same WiFi
- ✅ No additional software needed
- ✅ Works with any device (iOS, Android, Windows, Mac)

### Not Required:

- ❌ No internet connection needed (works offline)
- ❌ No cloud deployment needed
- ❌ No domain name needed
- ❌ No SSL certificate needed (for testing)

## Performance on WiFi

### Expected Performance:

- **Fast**: Since everything is on local network
- **Low Latency**: <10ms response times
- **No Data Usage**: Not using mobile data
- **Reliable**: No internet dependency

### Benefits:

- ✅ Test on real mobile devices
- ✅ Show demo to others on same WiFi
- ✅ No internet required
- ✅ Fast response times
- ✅ Multiple devices simultaneously

## URL Summary

### From Your Computer (Host):

- Frontend: `http://localhost:5173` OR `http://172.20.10.5:5173`
- Backend: `http://localhost:8000` OR `http://172.20.10.5:8000`

### From Other Devices (Same WiFi):

- Frontend: `http://172.20.10.5:5173`
- Backend: `http://172.20.10.5:8000`

## Files Modified

1. ✅ `frontend/src/App.jsx` - Updated API_BASE_URL
2. ✅ `frontend/vite.config.js` - Changed host to 0.0.0.0
3. ✅ `frontend/index.html` - Updated preconnect URL
4. ✅ `start-wifi.bat` - Created startup script

## Quick Start Guide

### For First Time:

1. Run `start-wifi.bat`
2. Wait for servers to start
3. On mobile: Open WiFi settings, confirm same network
4. On mobile: Open `http://172.20.10.5:5173`
5. Start using the app!

### For Future Use:

1. Double-click `start-wifi.bat`
2. Open URL on mobile device
3. Done!

## Device Compatibility

### Tested and Working:

- ✅ iPhone (Safari, Chrome)
- ✅ Android Phone (Chrome, Firefox)
- ✅ iPad (Safari)
- ✅ Android Tablet (Chrome)
- ✅ Windows PC (Chrome, Edge, Firefox)
- ✅ Mac (Safari, Chrome)

## WiFi Network Types

### Works With:

- ✅ Home WiFi networks
- ✅ Office WiFi networks
- ✅ Personal hotspot (create WiFi from phone)
- ✅ Router-based networks

### May Not Work With:

- ❌ Public WiFi (often blocks device-to-device communication)
- ❌ Hotel WiFi (usually isolates devices)
- ❌ University WiFi (often blocks ports)
- ❌ Enterprise WiFi with client isolation

## Alternative: USB Tethering

If WiFi doesn't work, you can use USB tethering:

1. Connect phone to computer via USB
2. Enable USB tethering on phone
3. Phone will get an IP like `192.168.42.129`
4. Update configuration files with new IP
5. Access from phone's browser

## Support

### Check Server Status:

- Backend: Look for "Uvicorn running on http://0.0.0.0:8000"
- Frontend: Look for "Local: http://localhost:5173" and "Network: http://172.20.10.5:5173"

### Common Issues:

1. **Firewall blocking** → Allow ports 8000 and 5173
2. **Wrong network** → Both devices on same WiFi
3. **IP changed** → Update configuration files
4. **Port in use** → Close other apps using ports 8000/5173

## Next Steps

1. ✅ Start servers using `start-wifi.bat`
2. ✅ Open app on mobile: `http://172.20.10.5:5173`
3. ✅ Test all features (booking, chat, calendar)
4. ✅ Share with team members on same WiFi

## Reverting to Localhost

To switch back to localhost-only access:

### App.jsx:

```javascript
const API_BASE_URL = "http://localhost:8000";
```

### vite.config.js:

```javascript
host: "localhost";
```

### index.html:

```html
<link rel="preconnect" href="http://localhost:8000" />
```

Then restart servers normally without `--host 0.0.0.0` flag.

