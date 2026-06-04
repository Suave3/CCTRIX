#!/usr/bin/env python3
import urllib.request
import urllib.error
import socket

camera_ip = "192.168.1.12"
username = "CCTRIX"
password = "ThanksForWatching"

print("Testing V380 camera HTTP connectivity...\n")

# Test different HTTP endpoints
http_endpoints = [
    f"http://{camera_ip}/",
    f"http://{camera_ip}:80/",
    f"http://{camera_ip}:8080/",
    f"http://{camera_ip}:81/",
]

for endpoint in http_endpoints:
    print(f"Testing: {endpoint}")
    try:
        # Create password manager for authentication
        password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, camera_ip, username, password)
        handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
        opener = urllib.request.build_opener(handler)
        
        response = opener.open(endpoint, timeout=5)
        print(f"✓ HTTP Response: {response.status}")
        print(f"  Headers: {dict(response.headers)}\n")
    except urllib.error.HTTPError as e:
        print(f"✗ HTTP Error {e.code}\n")
    except socket.timeout:
        print(f"✗ Timeout\n")
    except Exception as e:
        print(f"✗ Error: {str(e)[:60]}\n")

print("\nAlternative: Try accessing camera via mobile V380 app")
print("Check app settings for RTSP URL configuration")
