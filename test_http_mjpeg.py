#!/usr/bin/env python3
import cv2
import urllib.request
import base64

camera_ip = "192.168.1.12"
username = "CCTRIX"
password = "ThanksForWatching"

# Create basic auth header
credentials = base64.b64encode(f"{username}:{password}".encode()).decode()

print("Testing V380 camera HTTP/MJPEG alternatives...\n")

# Common V380 HTTP streaming URLs
urls = [
    # HTTP MJPEG streams
    f"http://{username}:{password}@{camera_ip}/mjpeg/video.mjpg",
    f"http://{username}:{password}@{camera_ip}:80/video",
    f"http://{username}:{password}@{camera_ip}:8080/mjpeg",
    f"http://{camera_ip}:8080/mjpeg?user={username}&pwd={password}",
    
    # Alternative RTSP ports/paths
    f"rtsp://{username}:{password}@{camera_ip}:554/stream1",
    f"rtsp://{username}:{password}@{camera_ip}:8554/stream",
]

for url in urls:
    print(f"Trying: {url}")
    try:
        cap = cv2.VideoCapture(url)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        # Try to grab a frame
        ret = cap.grab()
        if ret:
            print(f"  ✓ Stream connected!")
            ret, frame = cap.read()
            if ret:
                print(f"  ✓ SUCCESS! Frame received: {frame.shape}")
                cap.release()
                print(f"\n✓ WORKING URL: {url}\n")
                break
            else:
                print(f"  Connected but no frame yet\n")
        else:
            print(f"  Could not grab frame\n")
        cap.release()
    except Exception as e:
        print(f"  Error: {str(e)[:50]}\n")
