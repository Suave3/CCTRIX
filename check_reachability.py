#!/usr/bin/env python3
import subprocess
import time

camera_ip = "192.168.1.12"

print(f"Checking if {camera_ip} is still reachable...\n")

for attempt in range(3):
    try:
        result = subprocess.run(['ping', '-n', '1', camera_ip], capture_output=True, timeout=5)
        if result.returncode == 0:
            print(f"Attempt {attempt+1}: ✓ Ping successful")
        else:
            print(f"Attempt {attempt+1}: ✗ Ping failed")
        time.sleep(1)
    except Exception as e:
        print(f"Attempt {attempt+1}: Error - {e}")

print("\nIf pings work but no ports are open:")
print("1. Try power-cycling the camera (unplug 30 seconds)")
print("2. Press reset button on camera (if available)")
print("3. Check if camera is in sleep mode - look for power button")
print("4. Check IP address - camera may have changed IP")
print("5. Try accessing with different IP or using camera model name")
