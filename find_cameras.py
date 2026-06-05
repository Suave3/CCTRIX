import cv2
import numpy as np

print("=" * 60)
print("AVAILABLE CAMERA DEVICES")
print("=" * 60)

# Try devices 0-10
for device_id in range(10):
    try:
        # Try different backends
        for backend_name, backend in [("DSHOW", cv2.CAP_DSHOW), ("MSMF", cv2.CAP_MSMF), ("ANY", cv2.CAP_ANY)]:
            cap = cv2.VideoCapture(device_id, backend)
            
            if cap.isOpened():
                # Try to read a frame
                ret, frame = cap.read()
                
                # Get camera properties
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                
                cap.release()
                
                status = "✓ OPEN" if ret else "✓ OPEN (no frame)"
                print(f"\nDevice {device_id} ({backend_name}): {status}")
                print(f"  Resolution: {width}x{height}")
                print(f"  FPS: {fps}")
                break
            else:
                cap.release()
    except Exception as e:
        pass

print("\n" + "=" * 60)
print("LOOK FOR OBS VIRTUAL CAMERA (should have 'OBS' in name)")
print("Or try different device numbers in CAMERA_SOURCE=X")
print("=" * 60)
