#!/usr/bin/env python3
import cv2
import time

# V380 camera streaming URLs to test
urls_to_test = [
    "rtsp://admin:12345@192.168.1.12:554/stream",
    "rtsp://admin:admin@192.168.1.12:554/stream",
    "rtsp://admin:12345@192.168.1.12:554/stream1",
    "rtsp://admin:admin@192.168.1.12:554/stream1",
    "rtsp://192.168.1.12:554/stream",
    "rtsp://192.168.1.12:554/stream1",
    "http://admin:12345@192.168.1.12:80/stream",
    "http://192.168.1.12:8080/mjpeg",
]

print("Testing V380 camera RTSP URLs...\n")

for url in urls_to_test:
    print(f"Testing: {url}")
    try:
        cap = cv2.VideoCapture(url)
        
        # Try to read a frame with timeout
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        ret, frame = cap.read()
        
        if ret and frame is not None:
            print(f"✓ SUCCESS! Working URL: {url}")
            print(f"  Frame size: {frame.shape}")
            cap.release()
            print("\nAdd this to your .env file:")
            print(f'CAMERA_SOURCE="{url}"')
            break
        else:
            print(f"✗ Connected but no frame\n")
            cap.release()
    except Exception as e:
        print(f"✗ Failed: {str(e)[:60]}\n")

print("If none worked, check:")
print("1. Camera IP address is correct")
print("2. Check the V380 manual for default credentials")
print("3. Try logging into the camera via mobile app to get correct URL")
