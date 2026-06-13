from flask import Flask, render_template, Response, request, redirect, url_for, session, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
import time
import os
import json
import urllib.request
import urllib.parse
import numpy as np
from datetime import datetime, date, timedelta
import psycopg2
from dotenv import load_dotenv
from PIL import Image
import database as db
import threading as threading_module
from queue import Queue

# Optional imports for GUI/camera functionality (may not be available in cloud)
try:
    import cv2
except ImportError:
    cv2 = None

# Screen capture imports removed - using OBS Virtual Camera instead

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "cctv_secret_key_change_in_prod")
app.static_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.static_url_path = "/static"

# reCAPTCHA v2 — uses Google's official test keys by default for local development.
# Replace with real keys from https://www.google.com/recaptcha/admin in production.
RECAPTCHA_SITE_KEY   = os.environ.get("RECAPTCHA_SITE_KEY",   "6LfrtQgtAAAAAKMSI7t2cyk9KDRiMd0lVEtf7ceJ")
RECAPTCHA_SECRET_KEY = os.environ.get("RECAPTCHA_SECRET_KEY", "6LfrtQgtAAAAADm5TxMPkeSiMBf6HIl8finN69Ak")

# =========================
# DATABASE CONNECTION & INITIALIZATION
# =========================

# Initialize database on startup (but don't crash if it fails)
try:
    db.init_db()
    print("✅ Database initialized successfully!")
except Exception as e:
    print(f"⚠️  Database init error: {e}")
    print("   Database will be retried on first request")

# =========================
# FOLDERS
# =========================
LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "logs")
os.makedirs(LOGS_DIR, exist_ok=True)
print(f"Logs directory: {LOGS_DIR}")

# =========================
# CAMERA & SCREEN CAPTURE
# =========================

# OBS Virtual Camera workflow - see _open_camera() function for details
# (ScreenCapture class no longer used - replaced with OBS Virtual Camera)

camera = None

# Frame buffer for threaded reading (VLC-style)
frame_buffer = Queue(maxsize=2)  # Keep only latest 2 frames
camera_reading_thread = None
camera_thread_stop = False

# =========================
# CAMERA SOURCE: RTSP or Local Device
# =========================
# 
# WORKFLOW:
# 1. Try to connect to RTSP camera (network stream)
# 2. If RTSP fails, fall back to local device camera (e.g., webcam)
# 3. If both fail, run in headless mode (no camera)
#
# SETUP:
# Use CAMERA_SOURCE=rtsp://... for RTSP network streams (primary)
# Use CAMERA_SOURCE=0 for local webcam/device camera (fallback)

CAMERA_SOURCE = os.environ.get("CAMERA_SOURCE", "0").strip()
FALLBACK_DEVICE = "0"  # Fallback to device 0 if RTSP fails

# Common RTSP stream paths to try as fallbacks
RTSP_FALLBACK_PATHS = [
    "/stream1",      # Original
    "/stream",
    "/ch0",
    "/ch1", 
    "/main",
    "/live",
    "/live/ch0",
    "/media/video1",
    "/h264/ch0/av_stream",
]

# OpenCV reads from RTSP streams or local device cameras
def _open_camera(source):
    # Skip camera if cv2 is not available (e.g., on Railway cloud)
    if cv2 is None:
        print("⚠️  OpenCV (cv2) not available - running in headless mode")
        return None
    
    try:
        # Check if source is a local device (numeric) or network stream (RTSP)
        if source.isdigit():
            # Local device camera
            print(f"🎥 Attempting to open local device camera (device {source})...")
            backends = [getattr(cv2, 'CAP_DSHOW', None), getattr(cv2, 'CAP_MSMF', None), getattr(cv2, 'CAP_ANY', None)]
            for backend in backends:
                if backend is None:
                    continue
                cam = cv2.VideoCapture(int(source), backend)
                if cam is not None and cam.isOpened():
                    print(f"✓ Local device camera opened successfully (device {source}) with backend {backend}")
                    return cam
                if cam is not None:
                    cam.release()
            print(f"✗ Failed to open local device camera (device {source})")
            return None

        # For network streams (RTSP/HTTP)
        print(f"🎥 Attempting to connect to RTSP stream: {source}")
        
        # Extract base URL for fallback attempts
        is_rtsp = source.startswith("rtsp://") or source.startswith("http://")
        if is_rtsp and "@" in source:
            # Extract protocol and credentials
            base_url = source[:source.rfind("/")]
            
            # Try original path first, then fallback paths
            urls_to_try = [source]
            
            # Add fallback paths by replacing the stream path
            for fallback_path in RTSP_FALLBACK_PATHS:
                fallback_url = base_url + fallback_path
                if fallback_url not in urls_to_try:
                    urls_to_try.append(fallback_url)
        else:
            urls_to_try = [source]
        
        # Try each URL with FAST timeout
        for attempt_url in urls_to_try:
            if attempt_url != urls_to_try[0]:  # Not the primary URL
                print(f"  Trying fallback path: {attempt_url.split('/')[-1] or '/'}")
            
            backends = []
            if hasattr(cv2, 'CAP_FFMPEG'):
                backends.append(('FFMPEG', cv2.CAP_FFMPEG))
            if hasattr(cv2, 'CAP_GSTREAMER'):
                backends.append(('GSTREAMER', cv2.CAP_GSTREAMER))
            backends.append(('DEFAULT', getattr(cv2, 'CAP_ANY', None)))

            for backend_name, backend in backends:
                if backend is None:
                    continue
                
                cam = cv2.VideoCapture(attempt_url, backend)
                if cam is None:
                    continue
                
                # Set optimized properties for network streams (RTSP)
                if hasattr(cam, 'set'):
                    try:
                        cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffer for low latency
                    except Exception:
                        pass
                    try:
                        if hasattr(cv2, 'CAP_PROP_OPEN_TIMEOUT_MSEC'):
                            cam.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 10000)  # 10s timeout for RTSP
                    except Exception:
                        pass
                    try:
                        cam.set(cv2.CAP_PROP_FPS, 30)  # Request 30 FPS
                    except Exception:
                        pass
                    try:
                        cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                        cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    except Exception:
                        pass
                    try:
                        cam.set(cv2.CAP_PROP_AUTOFOCUS, 0)
                    except Exception:
                        pass
                
                # Give RTSP stream time to stabilize (2-3 seconds)
                print(f"    {backend_name}: Testing stream connection...")
                time.sleep(3)
                
                if cam.isOpened():
                    print(f"    {backend_name}: Attempting to read first frame...")
                    # Try to read a frame to verify connection (with 5 attempts)
                    frame_success = False
                    for attempt in range(5):
                        ret, frame = cam.read()
                        if ret and frame is not None and frame.size > 0:
                            frame_success = True
                            print(f"✓ RTSP camera connected successfully!")
                            print(f"  URL: {attempt_url}")
                            print(f"  Backend: {backend_name}")
                            return cam
                        time.sleep(0.5)
                    
                    if not frame_success:
                        print(f"    {backend_name}: Stream opened but can't read frames (trying next backend)")
                        cam.release()
                else:
                    print(f"    {backend_name}: Failed to open stream")
                    cam.release()

        print(f"✗ All connection methods failed for RTSP: {source}")
        print("   Network-accessible cameras only work when:")
        print("   1. Camera is publicly accessible (port forwarded)")
        print("   2. You're in the same network as the camera")
        print("   3. Railway can route to your network")
        print("")
        print("   TEST: To verify RTSP works, try setting:")
        print("   CAMERA_SOURCE=rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mov")
        return None
        
    except Exception as e:
        print(f"CAMERA OPEN ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

if CAMERA_SOURCE:
    print(f"Attempting camera source: {CAMERA_SOURCE}")
    # Try camera in background to not block app startup
    def _init_camera():
        global camera, camera_thread_stop, camera_reading_thread
        try:
            camera = _open_camera(CAMERA_SOURCE)
            
            # Fallback to local device if RTSP or primary source fails
            if camera is None and not CAMERA_SOURCE.isdigit():
                print(f"⚠️  Primary source failed. Falling back to local device camera (device {FALLBACK_DEVICE})...")
                camera = _open_camera(FALLBACK_DEVICE)
            
            if camera is None:
                print("⚠️  CAMERA ERROR: Unable to open camera source - running in headless mode")
            else:
                # START READER THREAD ONLY AFTER CAMERA IS READY
                camera_thread_stop = False
                camera_reading_thread = threading_module.Thread(target=_camera_reader_thread, daemon=True)
                camera_reading_thread.start()
                print("✓ Frame reader thread started")
        except Exception as e:
            print(f"⚠️  Camera init error: {e}")
    
    # Start camera init in background thread (non-blocking)
    camera_init_thread = threading_module.Thread(target=_init_camera, daemon=True)
    camera_init_thread.start()
else:
    print("⚠️  CAMERA_SOURCE not set - running in headless mode")

previous_frame = None
motion_active = False
last_capture_time = 0
last_motion_time = 0
stable_motion_state = False
last_detection_log_time = 0  # Track when we last logged a detection (for continuous logging every 1 second)
current_timestamp = ""  # Store timestamp for all frames
current_status = "NO MOTION DETECTED"  # Store status for all frames
current_status_color = (255, 255, 255)  # Store status color for all frames
last_rects = []  # Store motion rectangles for display on skipped frames

# =========================
# DEDICATED CAMERA READING THREAD (VLC-STYLE)
# =========================
def _camera_reader_thread():
    """Continuously read frames from camera without blocking (like VLC)"""
    global camera_thread_stop, frame_buffer
    
    if camera is None:
        return
    
    print("📹 Camera reader thread started")
    
    while not camera_thread_stop:
        try:
            ret, frame = camera.read()
            
            if not ret or frame is None:
                # Connection lost, try to reconnect
                print("⚠️  Camera frame read failed - waiting...")
                time.sleep(0.5)
                continue
            
            # Drop old frames if buffer is full (prevent lag buildup like VLC does)
            try:
                frame_buffer.put_nowait(frame)
            except:
                # Buffer full - drop oldest frame and add new one
                try:
                    frame_buffer.get_nowait()
                    frame_buffer.put_nowait(frame)
                except:
                    pass
            
        except Exception as e:
            print(f"Camera reader error: {e}")
            time.sleep(0.1)
    
    print("📹 Camera reader thread stopped")


# Start camera reader thread if camera is available
# NOTE: This is now started inside _init_camera() after successful connection


# =========================
# ASYNC DATABASE LOGGING
# =========================
db_log_queue = Queue(maxsize=100)

def _async_db_logger():
    """Background threacd for database logging to avoid blocking video stream"""
    while True:
        try:
            log_item = db_log_queue.get(timeout=1)
            if log_item is None:  # Shutdown signal
                break
            
            log_type, args = log_item
            try:
                if log_type == 'detection':
                    db.log_detection(*args)
                    print(f"✓ Async: Detection logged")
                elif log_type == 'auth':
                    db.log_auth(*args)
                    print(f"✓ Async: Auth logged - {args[0]} {args[1]}")
                elif log_type == 'failed_login':
                    db.log_failed_login(*args)
                    print(f"✓ Async: Failed login logged - {args[0]}")
            except Exception as e:
                print(f"❌ Async logging error: {e}")
                import traceback
                traceback.print_exc()
        except:
            pass

# Start async logger thread
logger_thread = threading_module.Thread(target=_async_db_logger, daemon=True)
logger_thread.start()

# =========================
# BRUTE FORCE PROTECTION - IN-MEMORY TRACKING
# =========================
import time as time_module
from collections import defaultdict

# Track failed login attempts per IP: {ip: [(timestamp, username), ...]}
FAILED_ATTEMPTS = defaultdict(list)

def log_failed_attempt(ip, username):
    """Log a failed login attempt for an IP (in-memory + database)"""
    current_time = time_module.time()
    
    # Add to in-memory tracking
    FAILED_ATTEMPTS[ip].append((current_time, username))
    
    # Clean up old attempts (older than 10 minutes)
    cutoff_time = current_time - (10 * 60)
    FAILED_ATTEMPTS[ip] = [(t, u) for t, u in FAILED_ATTEMPTS[ip] if t > cutoff_time]
    
    # Also log to database (async)
    try:
        db.log_failed_login(username, ip, "")
    except Exception as e:
        print(f"Note: Could not log to database: {e}")
    
    print(f"✓ Failed attempt logged: {username} from {ip} - Total in window: {len(FAILED_ATTEMPTS[ip])}")
    return len(FAILED_ATTEMPTS[ip])

def get_failed_attempt_count(ip):
    """Get count of failed attempts for an IP in the last 10 minutes (in-memory)"""
    current_time = time_module.time()
    cutoff_time = current_time - (10 * 60)
    
    # Clean up old attempts
    if ip in FAILED_ATTEMPTS:
        FAILED_ATTEMPTS[ip] = [(t, u) for t, u in FAILED_ATTEMPTS[ip] if t > cutoff_time]
    
    count = len(FAILED_ATTEMPTS.get(ip, []))
    print(f"DEBUG: IP {ip} has {count} failed attempts in last 10 minutes")
    return count

def is_ip_blocked(ip):
    """Check if an IP is blocked due to too many failed login attempts"""
    count = get_failed_attempt_count(ip)
    if count >= 5:
        print(f"🚫 IP BLOCKED: {ip} has {count} failed attempts")
        return True
    return False

def get_ip_block_time_remaining(ip):
    """Get remaining block time for an IP in seconds"""
    if not FAILED_ATTEMPTS.get(ip):
        return 0
    
    # Get the earliest attempt
    earliest_time = min([t for t, u in FAILED_ATTEMPTS[ip]])
    block_end = earliest_time + (10 * 60)
    remaining = block_end - time_module.time()
    return max(0, int(remaining))

# =========================
# RECAPTCHA VERIFIER
# =========================
def _verify_recaptcha(token, ip):
    # Require a token, even in test/local mode.
    if not token or not token.strip():
        return False

    # If using Google's official test keys, accept any non-empty token for local dev.
    if RECAPTCHA_SECRET_KEY == "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ17ZFtSe":
        return True

    try:
        data = urllib.parse.urlencode({
            "secret": RECAPTCHA_SECRET_KEY,
            "response": token,
            "remoteip": ip,
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://www.google.com/recaptcha/api/siteverify",
            data=data, method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result.get("success", False)
    except Exception as e:
        print("reCAPTCHA error:", e)
        return False

# =========================
# AUTH LOGGER
# =========================
def _log_auth(username, action, reason, ip, user_agent):
    """Log authentication events to database (async, non-blocking)"""
    try:
        db_log_queue.put_nowait(('auth', (username, action, reason, ip, user_agent)))
    except:
        print(f"Auth log queue full, skipping log for {username}")

# =========================
# ROLE GUARD
# =========================
def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated

# =========================
# LOGIN
# =========================
@app.route('/login', methods=['GET', 'POST'])
def login():
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent')

    def _render_login(error=None, attempts_remaining=None):
        return render_template("login.html", error=error, site_key=RECAPTCHA_SITE_KEY, attempts_remaining=attempts_remaining)

    if request.method == 'POST':

        # Check if IP is already blocked
        if is_ip_blocked(ip):
            remaining = get_ip_block_time_remaining(ip)
            minutes = remaining // 60
            seconds = remaining % 60
            error_msg = f"🚫 Too many failed login attempts. Your IP is blocked for {minutes}m {seconds}s."
            return _render_login(error_msg)

        # reCAPTCHA check
        recaptcha_token = request.form.get('g-recaptcha-response', '')
        if not _verify_recaptcha(recaptcha_token, ip):
            return _render_login("Please complete the reCAPTCHA verification.")

        username = request.form.get('username')
        password = request.form.get('password')

        # Try to get user from database
        user = None
        try:
            result = db.execute_query(
                "SELECT id, password_hash, role FROM users WHERE username = %s",
                (username,),
                fetch=True
            )
            if result:
                user = result[0]
        except Exception as e:
            print("DB ERROR:", e)

        # Check if password is correct
        if user and check_password_hash(user[1], password):
            session['logged_in'] = True
            session['username'] = username
            session['role'] = user[2]
            _log_auth(username, 'LOGIN_SUCCESS', 'Valid credentials', ip, user_agent)
            print(f"✅ LOGIN SUCCESS: {username} from {ip}")
            return redirect(url_for('index'))

        # PASSWORD IS WRONG - log the failed attempt
        print(f"\n{'='*60}")
        print(f"❌ LOGIN FAILED: Invalid credentials for {username} from {ip}")
        print(f"{'='*60}")
        
        # Log to failed attempts (in-memory)
        current_count = log_failed_attempt(ip, username)
        print(f"Total failed attempts for IP {ip}: {current_count}/5")
        
        # Also log to auth logs asynchronously
        _log_auth(username, 'LOGIN_FAILED', 'Invalid credentials', ip, user_agent)
        
        # Check if they're now blocked
        if current_count >= 5:
            remaining = get_ip_block_time_remaining(ip)
            minutes = remaining // 60
            seconds = remaining % 60
            error_msg = f"🚫 Too many failed login attempts. Your IP is blocked for {minutes}m {seconds}s."
            print(f"🚫 BLOCKING IP: {ip}")
            return _render_login(error_msg)
        
        # Show how many attempts remain
        attempts_remaining = 5 - current_count
        if attempts_remaining == 1:
            error_msg = f"❌ Invalid username or password. ⚠️ ONE ATTEMPT REMAINING before 10-minute lockout!"
        else:
            error_msg = f"❌ Invalid username or password. ({attempts_remaining} attempts remaining)"
        
        print(f"INFO: User has {attempts_remaining} attempts left")
        return _render_login(error_msg, attempts_remaining)

    return _render_login()

# =========================
# LOGOUT
# =========================
@app.route('/logout')
def logout():
    username = session.get('username', 'unknown')
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    _log_auth(username, 'LOGOUT', 'User logged out', ip, user_agent)
    session.clear()
    return redirect(url_for('login'))

# =========================
# DASHBOARD
# =========================
@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template("index.html", role=session.get('role'), username=session.get('username', ''))

# =========================
# VIDEO STREAM
# =========================
def generate_frames():

    global previous_frame
    global motion_active
    global last_capture_time
    global last_motion_time
    global stable_motion_state
    global last_detection_log_time
    global current_timestamp
    global current_status
    global current_status_color
    global last_rects

    # Check if OpenCV is available
    if cv2 is None:
        print("⚠️  OpenCV not available - cannot generate video stream")
        while True:
            blank = np.ones((500, 800, 3), dtype=np.uint8) * 50
            cv2_available = False
            try:
                import cv2 as cv2_test
                cv2_available = True
            except:
                pass
            if cv2_available:
                cv2.putText(blank, "ERROR: OpenCV import failed", (50, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            ret, buffer = cv2.imencode('.jpg', blank, [cv2.IMWRITE_JPEG_QUALITY, 70]) if cv2 else (False, None)
            if ret and buffer is not None:
                yield (
                    b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n'
                    + buffer.tobytes() +
                    b'\r\n'
                )
            else:
                # Fallback: no cv2 available, just black frame
                yield (
                    b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n'
                    + b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xFF\xDB\x00C\x00\x03\x02\x02\x02\x02\x02\x03\x02\x02\x02\x03\x03\x03\x03\x04\x06\x04\x04\x04\x04\x04\x08\x06\x06\x05\x06\x09\x08\n\n\t\x08\t\t\n\x0c\x0f\x0c\n\x0b\x0e\x0b\n\n\n\x0c\x11\r\x0e\x0f\x10\x10\x11\x10\n\n\x11\x11\x12\x12\x12\x13\x0f\x13\x13\x13\x13\x13\x13\x13\x13\x13\x13\x13\x13\x13\x13\x13\x13\x13\x13\x13\x13\x13\x13\x13\x13\x13\x13\xFF\xC0\x00\x0B\x08\x00\x01\x00\x01\x01\x01\x11\x00\xFF\xC4\x00\x1F\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xFF\xC4\x00\xB5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xFF\xDA\x00\x08\x01\x01\x00\x00?\x00\xfb\xd5U\x00\x00\x00\x01\xFF\xD9' +
                    b'\r\n'
                )
            time.sleep(0.1)
        return

    # Railway mode - no camera, but simulate motion events for demo
    if camera is None:
        print("⚠️  HEADLESS MODE: No camera available (Railway cloud) - Generating test motion events for demo")
        
        import random
        demo_event_counter = 0
        demo_last_event = time.time()
        demo_motion_active = False
        
        while True:
            # Simulate motion events every 15-30 seconds for demo purposes
            current_time = time.time()
            if current_time - demo_last_event > random.randint(15, 30):
                demo_motion_active = not demo_motion_active
                demo_last_event = current_time
                
                if demo_motion_active:
                    # Log a motion detection event (simulated)
                    try:
                        # Use proper log_detection signature: (person_detected, confidence, image_path)
                        db_log_queue.put_nowait(('detection', (True, 0.95, 'demo_snapshot.jpg')))
                        demo_event_counter += 1
                    except Exception as e:
                        print(f"Demo logging error: {e}")
            
            # Display message with event count
            blank = np.ones((500, 800, 3), dtype=np.uint8) * 50
            cv2.putText(blank, "Railway Cloud Mode", (120, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 165, 255), 2)
            cv2.putText(blank, "No Camera Connected", (80, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.putText(blank, "Logs are still recording", (70, 350), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 1)
            
            # Show demo event status
            status_text = "TEST EVENTS ACTIVE" if demo_motion_active else "TEST READY"
            status_color = (0, 255, 0) if demo_motion_active else (100, 100, 100)
            cv2.putText(blank, status_text, (200, 430), cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 1)
            cv2.putText(blank, f"Events: {demo_event_counter}", (300, 470), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 255, 0), 1)
            
            ret, buffer = cv2.imencode('.jpg', blank, [cv2.IMWRITE_JPEG_QUALITY, 70])
            frame_bytes = buffer.tobytes()
            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n'
                + frame_bytes +
                b'\r\n'
            )
            time.sleep(0.5)
        return

    # ===== ULTRA-AGGRESSIVE OPTIMIZATION PARAMETERS =====
    FRAME_SKIP = 8  # Process every 8th frame (87.5% reduction in detection processing)
    DISPLAY_WIDTH, DISPLAY_HEIGHT = 480, 270  # Ultra-low resolution for lightning-fast encoding
    BLUR_KERNEL = 3  # Minimal blur
    MIN_CONTOUR_AREA = 1200  # Very high threshold reduces false positives
    MOTION_THRESHOLD = 30  # High threshold = less noise
    JPEG_QUALITY = 15  # Ultra-compressed JPEG (maximum speed)
    MAX_FPS = 20  # Reduce to 20 fps for network efficiency
    FRAME_TIME = 1.0 / MAX_FPS  # Time between frames
    
    frame_count = 0
    last_frame_time = time.time()
    cached_display = None  # Cache the last encoded frame

    while True:
        try:
            # Non-blocking read from frame buffer (VLC-style threaded reading)
            try:
                frame = frame_buffer.get(timeout=0.5)  # 500ms timeout
            except:
                # No frame available - show waiting message
                blank = np.ones((DISPLAY_HEIGHT, DISPLAY_WIDTH, 3), dtype=np.uint8) * 50
                cv2.putText(blank, "Waiting for stream...", (80, 135), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                ret, buffer = cv2.imencode('.jpg', blank, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
                if ret:
                    yield (
                        b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n'
                        + buffer.tobytes() +
                        b'\r\n'
                    )
                time.sleep(0.1)
                continue

            frame_count += 1
            # SKIP FRAMES: Only process every Nth frame
            if frame_count % FRAME_SKIP != 0:
                # For skipped frames, reuse cached encoded frame (zero processing)
                if cached_display:
                    yield (
                        b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n'
                        + cached_display +
                        b'\r\n'
                    )
                continue

            # === DETECTION PROCESSING (runs every FRAME_SKIP frames) ===
            frame = cv2.flip(frame, 1)
            frame = cv2.resize(frame, (DISPLAY_WIDTH, DISPLAY_HEIGHT))
            display = frame.copy()
            clean = frame.copy()

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Skip blur entirely for max speed - threshold is sufficient
            
            if previous_frame is None:
                previous_frame = gray
                # Minimal text rendering for first frame
                current_timestamp = datetime.now().strftime("%H:%M:%S")
                current_status = "INIT"
                cv2.putText(display, f"[{current_status}]", (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                cv2.putText(display, current_timestamp, (8, 265), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 0), 1)
                ret, buffer = cv2.imencode('.jpg', display, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
                if ret:
                    cached_display = buffer.tobytes()
                    yield (
                        b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n'
                        + cached_display +
                        b'\r\n'
                    )
                continue

            diff = cv2.absdiff(previous_frame, gray)
            thresh = cv2.threshold(diff, MOTION_THRESHOLD, 255, cv2.THRESH_BINARY)[1]
            
            # ULTRA-MINIMAL: No morphological operations - direct threshold
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

            motion = False
            last_rects = []  # Reset rectangles for this frame
            
            for c in contours:
                area = cv2.contourArea(c)
                if area < MIN_CONTOUR_AREA:
                    continue
                
                x, y, w, h = cv2.boundingRect(c)
                
                # Quick filter: skip if too small
                if w < 30 or h < 30:
                    continue
                    
                motion = True
                last_rects.append((x, y, w, h))
                cv2.rectangle(display, (x, y), (x + w, y + h), (0, 255, 0), 1)
                break  # Only draw first contour to save time

            previous_frame = gray
            now = time.time()

            if motion:
                last_motion_time = now
                stable_motion_state = True

                # Log detection every 3 seconds to reduce I/O
                if (now - last_detection_log_time) > 3.0:
                    last_detection_log_time = now
                    filename = f"{int(now * 1000)}.jpg"
                    path = os.path.join(LOGS_DIR, filename)
                    image_path = f"/static/logs/{filename}"
                    
                    def save_image_async():
                        try:
                            cv2.imwrite(path, clean, [cv2.IMWRITE_JPEG_QUALITY, 20])
                            try:
                                db_log_queue.put_nowait(('detection', (True, 0.90, image_path)))
                            except:
                                pass
                        except:
                            pass
                    
                    save_thread = threading_module.Thread(target=save_image_async, daemon=True)
                    save_thread.start()

            # Stable motion state: clear after 1 second
            if now - last_motion_time > 1:
                stable_motion_state = False
                last_rects = []

            # Minimal text display
            current_status = "MOTION" if stable_motion_state else "IDLE"
            current_status_color = (0, 0, 255) if stable_motion_state else (255, 255, 255)
            current_timestamp = datetime.now().strftime("%H:%M:%S")

            cv2.putText(display, f"[{current_status}]", (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, current_status_color, 1)
            cv2.putText(display, current_timestamp, (8, 265), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 0), 1)

            # Ultra-aggressive JPEG encoding
            ret, buffer = cv2.imencode('.jpg', display, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])

            if ret:
                frame_bytes = buffer.tobytes()
                cached_display = frame_bytes
                yield (
                    b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n'
                    + frame_bytes +
                    b'\r\n'
                )
            
            # Strict frame rate limiting
            elapsed = time.time() - last_frame_time
            if elapsed < FRAME_TIME:
                time.sleep(FRAME_TIME - elapsed)
            last_frame_time = time.time()
            
        except Exception as e:
            print(f"Frame generation error: {e}")
            time.sleep(0.01)
            continue

# =========================
# VIDEO ROUTE
# =========================
@app.route('/video')
def video():

    if not session.get('logged_in'):

        return redirect(url_for('login'))

    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

# =========================
# MOTION IMAGE SERVING (with caching headers)
# =========================
@app.route('/api/motion-image/<filename>')
def motion_image(filename):
    """Serve motion detection snapshot images"""
    if not session.get('logged_in'):
        return jsonify({"error": "unauthorized"}), 401
    
    import os
    from flask import send_file
    
    # Validate filename to prevent directory traversal
    if '..' in filename or '/' in filename or '\\' in filename:
        return jsonify({"error": "invalid filename"}), 400
    
    file_path = os.path.join(LOGS_DIR, filename)
    
    # Verify file exists and is within logs directory
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        return jsonify({"error": "file not found"}), 404
    
    try:
        response = send_file(
            file_path,
            mimetype='image/jpeg',
            as_attachment=False,
            download_name=filename
        )
        # Prevent browser caching to show fresh images immediately
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    except Exception as e:
        print(f"Error serving image {filename}: {e}")
        return jsonify({"error": "could not serve image"}), 500

# =========================
# LOGS API
# =========================
@app.route('/logs')
def logs():
    if not session.get('logged_in'):
        return jsonify({"error": "unauthorized", "logs": []}), 401

    try:
        rows = db.get_recent_detections(20)
        motion_today = db.count_detections_today()

        return jsonify({
            "logs": [
                {
                    "person_detected": r[0],
                    "confidence": float(r[1]),
                    "image": r[2],
                    "image_filename": r[2].split('/')[-1] if r[2] else None,
                    "time": str(r[3])
                }
                for r in (rows or [])
            ],
            "motion_today": motion_today
        })

    except Exception as e:
        return jsonify({
            "error": str(e),
            "logs": [],
            "motion_today": 0
        })

# =========================
# FAILED LOGIN PAGE
# =========================
@app.route('/failed-logins-page')
@require_admin
def failed_logins_page():
    try:
        rows = db.get_recent_failed_logins(50)
        unique_ips = len(set(r[2] for r in (rows or []) if r[2]))
        return render_template("failed_logins.html", logs=rows or [], unique_ips=unique_ips, role=session.get('role'))
    except:
        return render_template("failed_logins.html", logs=[], unique_ips=0, role=session.get('role'))

# =========================
# AUTH LOGS API
# =========================
@app.route('/login_logs')
def login_logs():
    if not session.get('logged_in'):
        return jsonify({"error": "unauthorized", "logs": []}), 401
    if session.get('role') != 'admin':
        return jsonify({"logs": []})
    
    try:
        rows = db.get_recent_auth_logs(50)
        auth_today = db.count_auth_logs_today()

        return jsonify({
            "logs": [
                {
                    "username": r[0],
                    "type": r[1],
                    "reason": r[2],
                    "ip": r[3],
                    "time": str(r[4])
                }
                for r in (rows or [])
            ],
            "auth_today": auth_today
        })
    except Exception as e:
        return jsonify({"error": str(e), "logs": [], "auth_today": 0})

# =========================
# STATS API
# =========================
@app.route('/stats')
def stats():
    if not session.get('logged_in'):
        return jsonify({"error": "unauthorized"}), 401
    
    try:
        motion_today = db.count_detections_today()
        failed_today = db.count_failed_logins_today()
        auth_today = db.count_auth_logs_today()
        return jsonify({"motion_today": motion_today, "failed_logins_today": failed_today, "auth_events_today": auth_today})
    except Exception as e:
        return jsonify({"error": str(e), "motion_today": 0, "failed_logins_today": 0, "auth_events_today": 0})

# =========================
# EXPORT LOGS AS CSV (admin)
# =========================
@app.route('/export/motion')
@require_admin
def export_motion():
    from io import StringIO
    import csv as csv_mod
    output = StringIO()
    writer = csv_mod.writer(output)
    writer.writerow(['ID', 'Person Detected', 'Confidence', 'Image Path', 'Detected At'])
    try:
        rows = db.get_all_detections()
        for row in (rows or []):
            writer.writerow(row)
    except Exception as e:
        writer.writerow(['Error', str(e)])
    from flask import make_response
    resp = make_response(output.getvalue())
    resp.headers['Content-Type'] = 'text/csv'
    resp.headers['Content-Disposition'] = 'attachment; filename=motion_logs.csv'
    return resp

@app.route('/export/auth')
@require_admin
def export_auth():
    from io import StringIO
    import csv as csv_mod
    output = StringIO()
    writer = csv_mod.writer(output)
    writer.writerow(['ID', 'Username', 'Action', 'Reason', 'IP Address', 'User Agent', 'Timestamp'])
    try:
        rows = db.get_all_auth_logs()
        for row in (rows or []):
            writer.writerow(row)
    except Exception as e:
        writer.writerow(['Error', str(e)])
    from flask import make_response
    resp = make_response(output.getvalue())
    resp.headers['Content-Type'] = 'text/csv'
    resp.headers['Content-Disposition'] = 'attachment; filename=auth_logs.csv'
    return resp

# =========================
# SYSTEM STATUS (admin)
# =========================
@app.route('/system-status')
@require_admin
def system_status():
    db_ok = False
    try:
        result = db.execute_query("SELECT 1", fetch=True)
        db_ok = result is not None
    except Exception:
        pass
    
    cam_ok = camera is not None
    
    try:
        total_motion = db.count_total_detections()
        total_auth = db.count_total_auth_logs()
        total_users = db.count_total_users()
        total_failed = db.count_total_failed_logins()
    except Exception:
        total_motion = total_auth = total_users = total_failed = 0
    
    return render_template('system_status.html',
        db_ok=db_ok, cam_ok=cam_ok,
        total_motion=total_motion, total_auth=total_auth,
        total_users=total_users, total_failed=total_failed,
        role=session.get('role'))

# =========================
# HEALTH CHECK
# =========================
@app.route('/health')
def health():
    return jsonify({"status": "ok"})

# =========================
# DEBUG: Check failed login attempts (in-memory)
# =========================
@app.route('/debug/failed-logins/<ip_addr>')
def debug_failed_logins(ip_addr):
    """Debug endpoint to check failed login count for an IP"""
    try:
        count = get_failed_attempt_count(ip_addr)
        attempts = FAILED_ATTEMPTS.get(ip_addr, [])
        
        return jsonify({
            "ip": ip_addr,
            "failed_attempts_last_10min": count,
            "blocked": count >= 5,
            "attempts_remaining": max(0, 5 - count),
            "recent_attempts": [
                {
                    "username": username,
                    "timestamp": datetime.fromtimestamp(timestamp).isoformat()
                }
                for timestamp, username in attempts
            ]
        })
    except Exception as e:
        return jsonify({"error": str(e), "ip": ip_addr})

@app.route('/debug/clear-attempts/<ip_addr>')
def debug_clear_attempts(ip_addr):
    """DEBUG ONLY: Clear all failed attempts for an IP (for testing)"""
    if ip_addr in FAILED_ATTEMPTS:
        del FAILED_ATTEMPTS[ip_addr]
    return jsonify({"message": f"Cleared all attempts for {ip_addr}"})

@app.route('/debug/all-attempts')
def debug_all_attempts():
    """DEBUG ONLY: Show all tracked IPs and their attempt counts"""
    return jsonify({
        "tracked_ips": {
            ip: {
                "count": len(attempts),
                "blocked": len(attempts) >= 5,
                "attempts": [
                    {
                        "username": u,
                        "time": datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M:%S")
                    }
                    for t, u in attempts
                ]
            }
            for ip, attempts in FAILED_ATTEMPTS.items()
        }
    })


# =========================
# RUN APP
# =========================
if __name__ == '__main__':

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host='0.0.0.0',
        port=port
    )