# 🏥 WiFi Network Access - Quick Start

## 🚀 Quick Start

1. **Run the startup script:**

   ```
   Double-click: start-wifi.bat
   ```

2. **On your mobile device:**
   - Connect to the same WiFi network
   - Open browser
   - Go to: `http://192.168.137.173:5173`

That's it! 🎉

## 📱 Access URLs

### From Mobile/Tablet (Same WiFi):

```
http://192.168.137.173:5173
```

### From Your Computer:

```
http://localhost:5173
OR
http://192.168.137.173:5173
```

## ⚠️ Troubleshooting

### Can't connect?

1. ✅ Check both devices on same WiFi
2. ✅ Verify servers are running (2 terminal windows)
3. ✅ Disable VPN if active
4. ✅ Check Windows Firewall (allow ports 8000, 5173)

### IP Address Changed?

Run this command to find new IP:

```powershell
ipconfig | findstr /i "IPv4"
```

Then update the configuration files (see WIFI_NETWORK_SETUP.md)

## 📚 Full Documentation

See `WIFI_NETWORK_SETUP.md` for complete details, troubleshooting, and security notes.

## 🔒 Security Note

This setup is for local testing only. Devices must be on the same WiFi network. Not accessible from the internet.
