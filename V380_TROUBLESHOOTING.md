# V380 Camera Troubleshooting Guide

## Problem
OpenCV is timing out trying to connect to RTSP stream at:
`rtsp://CCTRIX:ThanksForWatching@192.168.1.12:554/live/ch00_01`

## Step-by-Step Troubleshooting

### Step 1: Verify Camera is Online
Run:
```
python quick_check.py
```
Should show which ports are open. If no ports are open, camera may be:
- Powered off
- Disconnected from network
- In sleep mode

### Step 2: Check Camera Web Interface
1. Open browser
2. Try: `http://192.168.1.12`
3. If it loads, login with: `CCTRIX` / `ThanksForWatching`
4. Look for settings menu to find streaming options

### Step 3: Try Alternative Streaming Methods

#### Option A: HTTP MJPEG (Most compatible)
Add to `.env`:
```
CAMERA_SOURCE=http://CCTRIX:ThanksForWatching@192.168.1.12:8080/mjpeg
```

#### Option B: Different RTSP Path
```
CAMERA_SOURCE=rtsp://CCTRIX:ThanksForWatching@192.168.1.12:554/stream1
CAMERA_SOURCE=rtsp://CCTRIX:ThanksForWatching@192.168.1.12:8554/stream
```

#### Option C: Alternative port
```
CAMERA_SOURCE=rtsp://CCTRIX:ThanksForWatching@192.168.1.12:8554/live/ch00_01
```

### Step 4: Use V380 Mobile App
If you have the V380 app installed:
1. Check if camera appears online
2. In camera settings, look for RTSP/streaming configuration
3. Note any URLs or parameters shown

### Step 5: Test Each URL
After modifying `.env`, run:
```
python app.py
```
And watch the console output for connection status.

### Step 6: Check Camera Manual/Sticker
V380 cameras often have:
- Default credentials printed on back
- Correct streaming URL format
- Support documentation

## Quick Test
```bash
# Test if camera responds to HTTP
curl -u CCTRIX:ThanksForWatching http://192.168.1.12

# Test if RTSP port is accessible
netstat -an | find ":554"
```

## Still Not Working?
1. Power cycle the camera (unplug 30 seconds, plug back in)
2. Reset camera to factory defaults (check manual)
3. Ensure camera firmware is up to date
4. Try temporarily disabling any firewall/antivirus

## Other V380 Resources
- Check back of camera or manual for manual URL
- V380 documentation: Look for "RTSP streaming" setup
- Try tech support from V380 vendor with camera model number
