#!/usr/bin/env python3
"""
RTSP Camera Connection Diagnostic Tool
Tests various connection methods and common stream paths
"""

import cv2
import time
import urllib.request
import urllib.error

# Camera credentials
USERNAME = "LEABINENE"
PASSWORD = "ThanksForWatching123"
IP = "192.168.1.13"
PORT = 554

# Common RTSP stream paths to try
STREAM_PATHS = [
    "/stream1",      # Your current path
    "/stream",
    "/ch0",
    "/ch1",
    "/main",
    "/live",
    "/live/ch0",
    "/media/video1",
    "/h264/ch0/av_stream",
    "/rtsp/ch0/main/av_stream",
]

def test_http_access():
    """Test if camera is accessible via HTTP"""
    print("\n" + "="*60)
    print("TEST 1: HTTP/Web Access to Camera")
    print("="*60)
    
    url = f"http://{IP}:{80}/"
    try:
        response = urllib.request.urlopen(url, timeout=5)
        print(f"✓ Camera web interface accessible at http://{IP}/")
        return True
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print(f"✗ Cannot access camera web interface: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_rtsp_path(full_url):
    """Test a specific RTSP URL"""
    print(f"\n  Testing: {full_url}")
    
    backends = [
        ("FFMPEG", cv2.CAP_FFMPEG),
        ("GSTREAMER", getattr(cv2, 'CAP_GSTREAMER', None)),
        ("DEFAULT", cv2.CAP_ANY),
    ]
    
    for backend_name, backend_id in backends:
        if backend_id is None:
            continue
            
        try:
            cam = cv2.VideoCapture(full_url, backend_id)
            
            if cam is not None:
                # Set properties
                cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                if hasattr(cv2, 'CAP_PROP_OPEN_TIMEOUT_MSEC'):
                    cam.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)
                
                time.sleep(2)
                
                if cam.isOpened():
                    # Try to read frames
                    for i in range(3):
                        ret, frame = cam.read()
                        if ret and frame is not None and frame.size > 0:
                            print(f"    ✓ {backend_name}: SUCCESS! Got frame {i+1}")
                            cam.release()
                            return True
                        time.sleep(0.5)
                    
                    cam.release()
                    print(f"    ✗ {backend_name}: Opened but no frames")
                else:
                    print(f"    ✗ {backend_name}: Failed to open")
        except Exception as e:
            print(f"    ✗ {backend_name}: {str(e)[:50]}")
    
    return False

def main():
    print("\n" + "="*60)
    print("RTSP CAMERA CONNECTION DIAGNOSTIC")
    print("="*60)
    print(f"Camera IP: {IP}:{PORT}")
    print(f"Username: {USERNAME}")
    
    # Test HTTP access first
    test_http_access()
    
    # Test RTSP paths
    print("\n" + "="*60)
    print("TEST 2: RTSP Stream Paths")
    print("="*60)
    
    found = False
    for path in STREAM_PATHS:
        url = f"rtsp://{USERNAME}:{PASSWORD}@{IP}:{PORT}{path}"
        if test_rtsp_path(url):
            print(f"\n✅ FOUND WORKING PATH: {path}")
            print(f"   Use this in your .env file:")
            print(f"   CAMERA_SOURCE={url}")
            found = True
            break
    
    if not found:
        print("\n" + "="*60)
        print("❌ No working RTSP paths found!")
        print("="*60)
        print("\nNext steps:")
        print("1. Check camera web interface at http://192.168.1.13")
        print("2. Look for RTSP settings in camera configuration")
        print("3. Verify username and password")
        print("4. Check if firewall is blocking port 554")
        print("5. Try accessing from another app (VLC, etc.)")

if __name__ == "__main__":
    main()
