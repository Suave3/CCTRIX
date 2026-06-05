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
import threading
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
RECAPTCHA_SITE_KEY   = os.environ.get("RECAPTCHA_SITE_KEY",   "6LdL4AgtAAAAACyhJQgVnU9kd4xzYfeAz-EYk9IU")
RECAPTCHA_SECRET_KEY = os.environ.get("RECAPTCHA_SECRET_KEY", "6LdL4AgtAAAAAJmX-CHFzJQBtG4-V7DAvK17yUMM")

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

# =========================
# CAMERA SOURCE: OBS Virtual Camera
# =========================
# 
# WORKFLOW:
# OBS Window Capture (in OBS app)
#        ↓
# OBS Virtual Camera output (enable in Tools > Start Virtual Camera)
#        ↓
# OpenCV (cv2.VideoCapture) reads virtual camera as device 0
#        ↓
# Flask video_feed streams to Dashboard
#
# BENEFITS:
# - OBS window can be minimized
# - Clean separation: OBS app handles capture, app handles streaming
# - Works even when OBS is not active
#
# SETUP:
# 1. Enable OBS Virtual Camera (Tools > Start Virtual Camera)
# 2. App detects it automatically as device 0
# 3. Done! Stream will show OBS output

# OBS Virtual Camera is the default (device 0).
# Use CAMERA_SOURCE=0 for OBS Virtual Camera (recommended)
# Use CAMERA_SOURCE=1 for a different camera device
# Use CAMERA_SOURCE=rtsp://... for RTSP network streams
CAMERA_SOURCE = os.environ.get("CAMERA_SOURCE", "0").strip()

# OpenCV reads from OBS Virtual Camera (numeric source) or RTSP streams
def _open_camera(source):
    # Skip camera if cv2 is not available (e.g., on Railway cloud)
    if cv2 is None:
        print("⚠️  OpenCV (cv2) not available - running in headless mode")
        return None
    
    try:
        
        if source.isdigit():
            print(f"🎥 Attempting to open OBS Virtual Camera (device {source})...")
            backends = [getattr(cv2, 'CAP_DSHOW', None), getattr(cv2, 'CAP_MSMF', None), getattr(cv2, 'CAP_ANY', None)]
            for backend in backends:
                if backend is None:
                    continue
                cam = cv2.VideoCapture(int(source), backend)
                if cam is not None and cam.isOpened():
                    print(f"✓ OBS Virtual Camera opened successfully (device {source}) with backend {backend}")
                    return cam
                if cam is not None:
                    cam.release()
            print(f"✗ Failed to open OBS Virtual Camera (device {source}). Make sure Virtual Camera is enabled in OBS (Tools > Start Virtual Camera)")
            return None

        # For network streams (RTSP/HTTP)
        backends = []
        if hasattr(cv2, 'CAP_GSTREAMER'):
            backends.append(cv2.CAP_GSTREAMER)
        if hasattr(cv2, 'CAP_FFMPEG'):
            backends.append(cv2.CAP_FFMPEG)
        backends.append(getattr(cv2, 'CAP_ANY', None))

        for backend in backends:
            if backend is None:
                continue
            print(f"Trying backend {backend} for {source}")
            cam = cv2.VideoCapture(source, backend)
            if cam is None:
                continue
            
            # Set optimized properties for network streams
            if hasattr(cam, 'set'):
                try:
                    cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    cam.set(cv2.CAP_PROP_AUTOFOCUS, 0)
                except Exception:
                    pass
                
                # Shorter timeout for network streams (5 seconds instead of 30)
                if hasattr(cv2, 'CAP_PROP_OPEN_TIMEOUT_MSEC'):
                    try:
                        cam.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)
                    except Exception:
                        pass
            
            # Wait a bit for connection to establish
            time.sleep(2)
            
            if cam.isOpened():
                # Try to read a frame to verify connection
                ret, frame = cam.read()
                if ret and frame is not None and frame.size > 0:
                    print(f"✓ Camera opened successfully: {source} with backend {backend}")
                    return cam
                else:
                    cam.release()
                    print(f"Camera open with backend {backend} but failed to read frame from: {source}")
            else:
                cam.release()
                print(f"Camera failed to open with backend {backend}: {source}")

        print(f"All backends failed for: {source}")
        return None
    except Exception as e:
        print("CAMERA OPEN ERROR:", e)
        return None

if CAMERA_SOURCE:
    print(f"Attempting camera source: {CAMERA_SOURCE}")
    camera = _open_camera(CAMERA_SOURCE)
    if camera is None:
        print("CAMERA ERROR: Unable to open camera source:", CAMERA_SOURCE)

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
                elif log_type == 'auth':
                    db.log_auth(*args)
                elif log_type == 'failed_login':
                    db.log_failed_login(*args)
            except Exception as e:
                print(f"Async logging error: {e}")
        except:
            pass

# Start async logger thread
logger_thread = threading.Thread(target=_async_db_logger, daemon=True)
logger_thread.start()

# =========================
# LOGIN CHECK - BRUTE FORCE PROTECTION
# =========================
def is_ip_blocked(ip):
    """
    Check if an IP is blocked due to too many failed login attempts.
    Policy: Block after 5 failed attempts within 10 minutes.
    """
    try:
        count = db.get_failed_login_attempts(ip, minutes=10)
        if count >= 5:
            print(f"🚫 IP BLOCKED: {ip} has {count} failed attempts in last 10 minutes")
            return True
        return False
    except Exception as e:
        print(f"IP block check error: {e}")
        return False

def get_ip_block_time_remaining(ip):
    """
    Get remaining block time for an IP in seconds.
    Returns 0 if not blocked.
    """
    try:
        from datetime import datetime, timedelta
        # Check most recent failed attempt
        query = """
            SELECT MAX(attempted_at) FROM failed_login_attempts
            WHERE ip_address = %s
        """
        result = db.execute_query(query, (ip,), fetch=True)
        if result and result[0][0]:
            last_attempt = result[0][0]
            if isinstance(last_attempt, str):
                last_attempt = datetime.fromisoformat(last_attempt)
            block_end = last_attempt + timedelta(minutes=10)
            remaining = (block_end - datetime.now()).total_seconds()
            return max(0, int(remaining))
        return 0
    except Exception as e:
        print(f"Block time calculation error: {e}")
        return 0

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
            return redirect(url_for('index'))

        # Password is wrong - log failed attempt SYNCHRONOUSLY so it's counted immediately
        try:
            result = db.log_failed_login(username, ip, user_agent)
            print(f"✓ Failed login logged: {username} from {ip} - Result: {result}")
        except Exception as e:
            print(f"❌ ERROR logging failed attempt: {e}")
            import traceback
            traceback.print_exc()
        
        # Also log to auth logs asynchronously
        _log_auth(username, 'LOGIN_FAILED', 'Invalid credentials', ip, user_agent)
        
        # Get current failure count for THIS IP - FORCE FRESH COUNT
        try:
            current_failures = db.get_failed_login_attempts(ip, minutes=10)
            print(f"DEBUG: IP {ip} has {current_failures} failed attempts in last 10 minutes")
        except Exception as e:
            print(f"❌ ERROR getting failure count: {e}")
            current_failures = 0
            import traceback
            traceback.print_exc()
        
        # If they've hit 5 failures, block them
        if current_failures >= 5:
            remaining = get_ip_block_time_remaining(ip)
            minutes = remaining // 60
            seconds = remaining % 60
            error_msg = f"🚫 Too many failed login attempts. Your IP is blocked for {minutes}m {seconds}s."
            print(f"🚫 IP BLOCKED: {ip} after {current_failures} attempts")
            return _render_login(error_msg)
        
        # Show how many attempts remain before lockout
        attempts_remaining = 5 - current_failures
        if attempts_remaining == 1:
            error_msg = "❌ Invalid username or password. ⚠️ ONE ATTEMPT REMAINING before 10-minute lockout!"
        else:
            error_msg = f"❌ Invalid username or password. ({attempts_remaining} attempts remaining)"
        
        print(f"DEBUG: Showing {attempts_remaining} attempts remaining to user")
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
            blank = np.ones((500, 800, 3), dtype=np.uint8) * 255
            from PIL import ImageDraw, ImageFont
            img = Image.fromarray(blank)
            draw = ImageDraw.Draw(img)
            draw.text((150, 240), "Video unavailable in cloud mode", fill=(0, 0, 255))
            frame_array = np.array(img)
            ret, buffer = cv2.imencode('.jpg', frame_array) if cv2 else (False, None)
            if ret and buffer is not None:
                yield (
                    b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n'
                    + buffer.tobytes() +
                    b'\r\n'
                )
            time.sleep(0.1)
        return

    # Railway mode - no camera
    if camera is None:
        while True:
            blank = np.ones((500, 800, 3), dtype=np.uint8) * 255
            cv2.putText(
                blank,
                "Railway Cloud Mode - No Camera",
                (120, 250),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2
            )
            ret, buffer = cv2.imencode('.jpg', blank, [cv2.IMWRITE_JPEG_QUALITY, 70])
            frame_bytes = buffer.tobytes()
            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n'
                + frame_bytes +
                b'\r\n'
            )
            time.sleep(0.1)
        return

    # ===== OPTIMIZATION PARAMETERS =====
    FRAME_SKIP = 1  # Process every frame for maximum accuracy
    BLUR_KERNEL = 5  # Smaller kernel for faster processing and better edge detection
    MIN_CONTOUR_AREA = 800  # Minimum area to reduce noise and false positives (green squares)
    MOTION_THRESHOLD = 15  # Lower threshold for higher sensitivity
    JPEG_QUALITY = 50  # JPEG compression quality (0-100, lower = faster and smaller files)
    MAX_FPS = 30  # Limit output to 30 fps for responsive display
    FRAME_TIME = 1.0 / MAX_FPS  # Time between frames
    
    frame_count = 0
    last_frame_time = time.time()

    while True:
        try:
            success, frame = camera.read()

            if not success:
                time.sleep(0.01)
                continue

            frame_count += 1
            
            # SKIP FRAMES: Only process every Nth frame
            if frame_count % FRAME_SKIP != 0:
                # Still encode and send, but skip detection processing
                display = cv2.flip(frame, 1)
                display = cv2.resize(display, (800, 500))
                
                # Add stored overlays to skipped frames for smooth display
                # Draw motion rectangles from last detection
                for rect in last_rects:
                    x, y, w, h = rect
                    cv2.rectangle(display, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
                # Add current status and timestamp to maintain continuous display
                if current_status:
                    cv2.putText(display, current_status, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, current_status_color, 2)
                if current_timestamp:
                    cv2.putText(display, current_timestamp, (20, 480), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                ret, buffer = cv2.imencode('.jpg', display, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (
                        b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n'
                        + frame_bytes +
                        b'\r\n'
                    )
                continue

            # === DETECTION PROCESSING (runs every FRAME_SKIP frames) ===
            frame = cv2.flip(frame, 1)
            frame = cv2.resize(frame, (800, 500))
            display = frame.copy()
            clean = frame.copy()

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # OPTIMIZATION: Smaller blur kernel for faster processing
            gray = cv2.GaussianBlur(gray, (BLUR_KERNEL, BLUR_KERNEL), 0)

            if previous_frame is None:
                previous_frame = gray
                # Still yield frame even if first frame
                current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                current_status = "Initializing..."
                current_status_color = (255, 255, 255)
                cv2.putText(display, current_status, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, current_status_color, 2)
                cv2.putText(display, current_timestamp, (20, 480), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                ret, buffer = cv2.imencode('.jpg', display, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (
                        b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n'
                        + frame_bytes +
                        b'\r\n'
                    )
                continue

            diff = cv2.absdiff(previous_frame, gray)
            thresh = cv2.threshold(diff, MOTION_THRESHOLD, 255, cv2.THRESH_BINARY)[1]
            # Better morphological operations for accurate motion detection
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            thresh = cv2.dilate(thresh, kernel, iterations=2)
            thresh = cv2.erode(thresh, kernel, iterations=1)  # Clean up noise
            # Additional dilation for better edge connectivity
            thresh = cv2.dilate(thresh, kernel, iterations=1)

            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            motion = False
            last_rects = []  # Reset rectangles for this frame
            for c in contours:
                area = cv2.contourArea(c)
                # Detect any motion above minimum threshold
                if area < MIN_CONTOUR_AREA:
                    continue
                
                # Filter out very elongated or thin contours (noise)
                x, y, w, h = cv2.boundingRect(c)
                aspect_ratio = float(w) / h if h > 0 else 0
                if aspect_ratio > 10 or aspect_ratio < 0.1:  # Skip extreme shapes
                    continue
                    
                motion = True
                last_rects.append((x, y, w, h))  # Store rectangle for display on skipped frames
                cv2.rectangle(display, (x, y), (x + w, y + h), (0, 255, 0), 2)

            previous_frame = gray
            now = time.time()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if motion:
                last_motion_time = now
                stable_motion_state = True

                # Log detection every 1 second of continuous motion (infinite logging)
                if (now - last_detection_log_time) > 1.0:
                    last_detection_log_time = now
                    # Use milliseconds to ensure unique filename even for rapid detections
                    filename = f"{int(now * 1000)}.jpg"
                    path = os.path.join(LOGS_DIR, filename)
                    # Save image SYNCHRONOUSLY to ensure file exists before logging
                    try:
                        cv2.imwrite(path, clean, [cv2.IMWRITE_JPEG_QUALITY, 50])
                    except Exception as e:
                        print(f"Error saving detection image: {e}")
                    image_path = f"/static/logs/{filename}"
                    
                    # OPTIMIZATION: Queue logging instead of blocking
                    try:
                        db_log_queue.put_nowait(('detection', (True, 0.90, image_path)))
                    except:
                        print("DB log queue full, skipping detection log")

            # Stable motion state: set to False only after 3 seconds without motion for faster clearing
            if now - last_motion_time > 3:
                stable_motion_state = False
                last_rects = []  # Clear rectangles when motion ends

            # Update global status and timestamp for display on all frames
            current_status = "MOTION DETECTED" if stable_motion_state else "NO MOTION DETECTED"
            current_status_color = (0, 0, 255) if stable_motion_state else (255, 255, 255)
            current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cv2.putText(display, current_status, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, current_status_color, 2)
            cv2.putText(display, current_timestamp, (20, 480), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            # OPTIMIZATION: Reduced JPEG quality for faster encoding
            ret, buffer = cv2.imencode('.jpg', display, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])

            if ret:
                frame_bytes = buffer.tobytes()
                yield (
                    b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n'
                    + frame_bytes +
                    b'\r\n'
                )
            
            # OPTIMIZATION: Frame rate limiting to avoid overwhelming clients
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
# DEBUG: Check failed login attempts
# =========================
@app.route('/debug/failed-logins/<ip_addr>')
def debug_failed_logins(ip_addr):
    """Debug endpoint to check failed login count for an IP"""
    try:
        count = db.get_failed_login_attempts(ip_addr, minutes=10)
        
        # Also fetch raw data to verify records exist
        query = """
            SELECT ip_address, attempted_at, username FROM failed_login_attempts
            WHERE ip_address = %s
            ORDER BY attempted_at DESC
            LIMIT 10
        """
        result = db.execute_query(query, (ip_addr,), fetch=True)
        
        return jsonify({
            "ip": ip_addr,
            "failed_attempts_last_10min": count,
            "recent_attempts": [
                {
                    "ip": r[0],
                    "timestamp": str(r[1]),
                    "username": r[2]
                }
                for r in (result or [])
            ]
        })
    except Exception as e:
        return jsonify({"error": str(e), "ip": ip_addr})


# =========================
# RUN APP
# =========================
if __name__ == '__main__':

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host='0.0.0.0',
        port=port
    )