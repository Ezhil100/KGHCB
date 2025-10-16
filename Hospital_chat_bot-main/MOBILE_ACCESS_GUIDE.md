# 📱 Mobile Access Instructions

## Step-by-Step Guide for Mobile Devices

### Step 1: Start the Server on Your Computer

1. On your computer, navigate to the project folder
2. Double-click `start-wifi.bat`
3. Two terminal windows will open (don't close them!)
4. Wait 5-10 seconds for servers to start

### Step 2: Connect Mobile to Same WiFi

1. On your mobile device, open WiFi settings
2. Make sure you're connected to the **same WiFi network** as your computer
3. Note: Public WiFi networks often block device-to-device connections

### Step 3: Open the App

1. Open your mobile browser (Safari, Chrome, etc.)
2. Type this address in the URL bar:
   ```
   http://192.168.137.173:5173
   ```
3. Press Go/Enter

### Step 4: Use the App!

- Select your role (Visitor, Staff, or Admin)
- Start chatting with the AI assistant
- Book appointments using the calendar
- All features work just like on desktop!

## 🎨 Features on Mobile

✅ **Fully Responsive Design**

- Optimized for all screen sizes
- Touch-friendly buttons (44px minimum)
- Smooth scrolling
- Calendar scales to fit screen

✅ **All Desktop Features**

- AI chatbot with RAG
- Appointment booking with calendar picker
- Quick actions buttons
- Real-time responses
- Admin dashboard (for admin role)

✅ **Mobile Optimizations**

- Prevents unwanted zoom on input focus
- Text wraps properly
- No horizontal scrolling
- Fast response times (local network)

## 📊 What You'll See

### Login Screen:

- Hospital logo at top
- Three role buttons:
  - 🚶 Visitor - For patients and guests
  - 👨‍⚕️ Staff - For hospital staff
  - 🔧 Admin - For administrators

### Chat Interface:

- Clean message bubbles
- Quick action buttons at bottom
- Text input with send button
- Real-time responses

### Appointment Booking:

- Step-by-step flow (5 steps)
- Calendar date picker (tap to select date)
- Time selection
- Reason input
- Confirmation with all details

## 🔧 Tips for Best Experience

### Browser Recommendations:

- **iOS**: Safari or Chrome
- **Android**: Chrome or Firefox
- Keep browser updated

### Network Tips:

- Use WiFi, not mobile data
- Stay on same network as computer
- Avoid public WiFi if possible
- Close unnecessary apps for best performance

### Display Tips:

- Use portrait or landscape mode
- Text scales automatically
- Zoom in/out if needed (app prevents unwanted zoom on inputs)
- Refresh page if something looks off

## 🐛 Common Issues

### "This site can't be reached"

**Solution:**

- Verify you're on the same WiFi as the computer
- Check that both server terminals are still running
- Try the address again (check for typos)

### Page loads but features don't work

**Solution:**

- Check browser console for errors
- Refresh the page (pull down to refresh)
- Make sure backend server is running (port 8000)

### Calendar doesn't appear

**Solution:**

- Refresh the page
- Try typing the date instead (fallback option)
- Check internet connection (although not required)

### Text too small or too large

**Solution:**

- Use browser zoom (pinch or zoom controls)
- Rotate device (portrait/landscape)
- App uses responsive fonts (automatically adjusts)

## 🔐 Privacy & Security

- ✅ All data stays on local network
- ✅ No internet connection required
- ✅ No data sent to external servers
- ✅ Fast and private
- ⚠️ Anyone on same WiFi can access

## 📞 Emergency Feature

The emergency call button works on mobile:

- Tap "Emergency: 📞 0422-2324105"
- Your phone will prompt to call
- Tap "Call" to dial

## 🎯 Testing Checklist

Try these features on your mobile:

- [ ] Login with Visitor role
- [ ] Send a chat message
- [ ] Ask about hospital services
- [ ] Click "Book Appointment" button
- [ ] Select date from calendar
- [ ] Complete appointment booking
- [ ] Try emergency call button
- [ ] Test in portrait mode
- [ ] Test in landscape mode
- [ ] Scroll through messages

## 📸 Sharing with Others

Want to show others on your WiFi?

1. Keep servers running on your computer
2. Share this URL with them:
   ```
   http://192.168.137.173:5173
   ```
3. They can access from their devices
4. Multiple users can use simultaneously

## 🔄 Stopping the Servers

When done testing:

1. Go back to your computer
2. In each terminal window, press `Ctrl + C`
3. Close the terminal windows
4. Mobile devices will no longer be able to connect

## 📧 Support

If you encounter issues:

1. Check `WIFI_NETWORK_SETUP.md` for detailed troubleshooting
2. Verify firewall settings on computer
3. Confirm WiFi network allows device-to-device communication
4. Try restarting servers
5. Check that IP address hasn't changed

## 🌟 Enjoy Testing!

Your Hospital AI Assistant is now accessible on your mobile device. Test all features, check the mobile responsive design, and share with your team for feedback!

**Current Setup:**

- Computer: Running servers at `192.168.137.173`
- Mobile: Access at `http://192.168.137.173:5173`
- Network: Same WiFi required
- Status: Ready to use! 🚀
