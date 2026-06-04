#!/usr/bin/env python3
import socket
import subprocess
import sys

camera_ip = "192.168.1.12"
ports_to_try = [80, 81, 82, 8000, 8080, 8081, 8888, 554, 8554]

print(f"Testing connectivity to camera at {camera_ip}...\n")

# Test 1: Ping the camera
print("1. PING TEST:")
try:
    result = subprocess.run(['ping', '-n', '1', camera_ip], capture_output=True, timeout=5)
    if result.returncode == 0:
        print(f"   ✓ Camera is REACHABLE\n")
    else:
        print(f"   ✗ Camera is NOT REACHABLE\n")
except Exception as e:
    print(f"   Error: {e}\n")

# Test 2: Try common HTTP ports
print("2. HTTP PORT SCAN:")
for port in ports_to_try:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((camera_ip, port))
        sock.close()
        
        if result == 0:
            print(f"   ✓ Port {port}: OPEN")
        else:
            print(f"   ✗ Port {port}: closed")
    except Exception as e:
        print(f"   ✗ Port {port}: Error - {e}")

print("\n3. COMMON RTSP URLS TO TRY:")
rtsp_urls = [
    "rtsp://192.168.1.12:554/stream",
    "rtsp://192.168.1.12:8554/stream",
    "rtsp://192.168.1.12:554/stream1",
    "rtsp://192.168.1.12:554/live",
    "rtsp://192.168.1.12/stream",
    "http://192.168.1.12:80/video",
    "http://192.168.1.12:8080/mjpeg",
    "http://192.168.1.12:8081/mjpeg",
]

for url in rtsp_urls:
    print(f"   - {url}")

print("\nInstructions:")
print("1. Check if camera is powered on")
print("2. Verify it's connected to the router with LAN cable")
print("3. Look for a manual or sticker on the camera with default credentials")
print("4. Once you find an open port, we can test the streaming URL")
