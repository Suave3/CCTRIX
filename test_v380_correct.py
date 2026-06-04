#!/usr/bin/env python3
import cv2
import time

credentials = "CCTRIX:ThanksForWatching@192.168.1.12"

# V380 camera URL variations to try
urls_to_test = [
    f"rtsp://{credentials}:554/live/ch00_01",
    f"rtsp://{credentials}:554/live/ch00_0",
    f"rtsp://{credentials}:554/stream",
    f"rtsp://{credentials}:554/stream1",
    f"rtsp://{credentials}:8554/live/ch00_01",
    f"rtsp://{credentials}:8554/stream",
    f"http://{credentials}:80/stream",
]

print("Testing V380 camera with correct credentials...\n")

for url in urls_to_test:
    print(f"Testing: {url}")
    try:
        cap = cv2.VideoCapture(url)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        # Try with shorter timeout
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
        
        ret, frame = cap.read()
        
        if ret and frame is not None:
            print(f"✓ SUCCESS! Working URL: {url}")
            print(f"  Frame size: {frame.shape}")
            cap.release()
            print("\nUpdate CAMERA_SOURCE to:")
            print(f'  {url}')
            break
        else:
            print(f"✗ Connected but no frame\n")
            cap.release()
    except Exception as e:
        print(f"✗ Failed: {str(e)[:60]}\n")
