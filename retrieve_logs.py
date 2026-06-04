#!/usr/bin/env python3
"""
CCTRIX Log Retrieval Tool
Retrieves and displays all logs from the database:
- Users
- Failed Logins
- Authentication Logs
- Detection Logs
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

print("=" * 100)
print("CCTRIX LOG RETRIEVAL TOOL")
print("=" * 100)

# Import database module
try:
    import database as db
    print("\n✅ Database module loaded successfully")
    print(f"✅ Database type: {db.DB_TYPE.upper()}")
except Exception as e:
    print(f"\n❌ Failed to import database module: {e}")
    sys.exit(1)

def format_timestamp(ts):
    """Format timestamp for display"""
    if ts is None:
        return "N/A"
    try:
        if isinstance(ts, str):
            return ts
        return str(ts)
    except:
        return str(ts)

def print_separator(title=""):
    """Print a separator line"""
    if title:
        print(f"\n{'=' * 100}")
        print(f"  {title}")
        print(f"{'=' * 100}")
    else:
        print("-" * 100)

# ============================================================================
# USERS
# ============================================================================
print_separator("1. REGISTERED USERS")

try:
    users_result = db.execute_query("SELECT * FROM users ORDER BY created_at DESC", fetch=True)
    
    if users_result:
        print(f"\nTotal Users: {len(users_result)}\n")
        print(f"{'ID':<5} {'Username':<20} {'Role':<15} {'Created At':<30}")
        print("-" * 70)
        
        for user in users_result:
            user_id = user[0] if isinstance(user, tuple) else user[0]
            username = user[1] if isinstance(user, tuple) else user[1]
            role = user[3] if isinstance(user, tuple) else user[3]
            created_at = format_timestamp(user[4] if isinstance(user, tuple) else user[4])
            
            print(f"{user_id:<5} {username:<20} {role:<15} {created_at:<30}")
    else:
        print("No users found in database")
except Exception as e:
    print(f"Error retrieving users: {e}")

# ============================================================================
# FAILED LOGIN ATTEMPTS
# ============================================================================
print_separator("2. FAILED LOGIN ATTEMPTS")

try:
    failed_logins = db.get_recent_failed_logins(100)
    
    if failed_logins:
        print(f"\nTotal Failed Attempts: {db.count_total_failed_logins()}\n")
        print(f"{'ID':<5} {'Username':<20} {'IP Address':<20} {'User Agent':<35} {'Attempted At':<30}")
        print("-" * 110)
        
        for login in failed_logins:
            login_id = login[0] if isinstance(login, tuple) else login[0]
            username = login[1] if isinstance(login, tuple) else login[1]
            ip_address = login[2] if isinstance(login, tuple) else login[2]
            user_agent = login[3] if isinstance(login, tuple) else login[3]
            attempted_at = format_timestamp(login[4] if isinstance(login, tuple) else login[4])
            
            # Truncate user agent if too long
            ua_display = user_agent[:32] + "..." if user_agent and len(user_agent) > 32 else user_agent or "N/A"
            
            print(f"{login_id:<5} {username:<20} {ip_address:<20} {ua_display:<35} {attempted_at:<30}")
        
        # Show today's failed logins
        today_failed = db.count_failed_logins_today()
        print(f"\n📊 Failed logins today: {today_failed}")
    else:
        print("No failed login attempts found in database")
except Exception as e:
    print(f"Error retrieving failed logins: {e}")

# ============================================================================
# AUTHENTICATION LOGS
# ============================================================================
print_separator("3. AUTHENTICATION LOGS")

try:
    auth_logs = db.get_recent_auth_logs(100)
    
    if auth_logs:
        print(f"\nTotal Auth Events: {db.count_total_auth_logs()}\n")
        print(f"{'ID':<5} {'Username':<20} {'Action':<20} {'Reason':<20} {'IP Address':<20} {'Timestamp':<30}")
        print("-" * 115)
        
        for log in auth_logs:
            log_id = log[0] if isinstance(log, tuple) else log[0]
            username = log[1] if isinstance(log, tuple) else log[1]
            action = log[2] if isinstance(log, tuple) else log[2]
            reason = log[3] if isinstance(log, tuple) else log[3]
            ip_address = log[4] if isinstance(log, tuple) else log[4]
            timestamp = format_timestamp(log[5] if isinstance(log, tuple) else log[5])
            
            # Truncate if needed
            reason_display = reason[:18] + ".." if reason and len(reason) > 18 else reason or "N/A"
            action_display = action[:18] if action else "N/A"
            
            print(f"{log_id:<5} {username:<20} {action_display:<20} {reason_display:<20} {ip_address:<20} {timestamp:<30}")
        
        # Show today's auth events
        today_auth = db.count_auth_logs_today()
        print(f"\n📊 Auth events today: {today_auth}")
    else:
        print("No authentication logs found in database")
except Exception as e:
    print(f"Error retrieving auth logs: {e}")

# ============================================================================
# DETECTION LOGS
# ============================================================================
print_separator("4. DETECTION LOGS")

try:
    detections = db.get_recent_detections(100)
    
    if detections:
        print(f"\nTotal Detections: {db.count_total_detections()}\n")
        print(f"{'ID':<5} {'Person Detected':<20} {'Confidence':<15} {'Image Path':<40} {'Detected At':<30}")
        print("-" * 110)
        
        for detection in detections:
            det_id = detection[0] if isinstance(detection, tuple) else detection[0]
            person_detected = detection[1] if isinstance(detection, tuple) else detection[1]
            confidence = detection[2] if isinstance(detection, tuple) else detection[2]
            image_path = detection[3] if isinstance(detection, tuple) else detection[3]
            detected_at = format_timestamp(detection[4] if isinstance(detection, tuple) else detection[4])
            
            # Format detection
            detected_str = "✅ YES" if person_detected else "❌ NO"
            confidence_str = f"{float(confidence):.2%}" if confidence else "N/A"
            
            # Truncate image path
            image_display = image_path[-35:] if image_path and len(image_path) > 35 else image_path or "N/A"
            
            print(f"{det_id:<5} {detected_str:<20} {confidence_str:<15} {image_display:<40} {detected_at:<30}")
        
        # Show today's detections
        today_detections = db.count_detections_today()
        print(f"\n📊 Detections today: {today_detections}")
    else:
        print("No detection logs found in database")
except Exception as e:
    print(f"Error retrieving detections: {e}")

# ============================================================================
# STATISTICS SUMMARY
# ============================================================================
print_separator("5. STATISTICS SUMMARY")

try:
    total_users = db.count_total_users()
    total_detections = db.count_total_detections()
    total_auth_logs = db.count_total_auth_logs()
    total_failed_logins = db.count_total_failed_logins()
    
    today_detections = db.count_detections_today()
    today_auth = db.count_auth_logs_today()
    today_failed = db.count_failed_logins_today()
    
    print(f"""
📊 OVERALL STATISTICS
├─ Total Users:           {total_users}
├─ Total Detections:      {total_detections}
├─ Total Auth Events:     {total_auth_logs}
└─ Total Failed Logins:   {total_failed_logins}

📅 TODAY'S STATISTICS
├─ Detections Today:      {today_detections}
├─ Auth Events Today:     {today_auth}
└─ Failed Logins Today:   {today_failed}
""")
except Exception as e:
    print(f"Error calculating statistics: {e}")

# ============================================================================
# EXPORT OPTION
# ============================================================================
print_separator("6. EXPORT OPTIONS")

print("""
💾 You can export logs through the web interface:
├─ Detection Logs:  GET /export/motion   (CSV format)
├─ Auth Logs:       GET /export/auth     (CSV format)
└─ Web Interface:   http://localhost:5000

Or use the database functions directly:
├─ get_recent_detections(limit)
├─ get_recent_auth_logs(limit)
├─ get_recent_failed_logins(limit)
└─ get_all_detections() / get_all_auth_logs()
""")

# ============================================================================
# DATABASE CONNECTION INFO
# ============================================================================
print_separator("7. DATABASE CONNECTION INFO")

db_type = os.environ.get("DB_TYPE", "sqlite").upper()
if db_type == "SQLITE":
    db_path = os.environ.get("DB_PATH", "./cctrix.db")
    print(f"""
📁 SQLite Database
├─ Type:     SQLite
├─ Path:     {db_path}
└─ Status:   ✅ Connected

To switch to PostgreSQL:
  python setup_db.py
  (Choose option 2 for local PostgreSQL)
""")
else:
    db_host = os.environ.get("DB_HOST", "N/A")
    db_port = os.environ.get("DB_PORT", "5432")
    db_name = os.environ.get("DB_NAME", "N/A")
    db_user = os.environ.get("DB_USER", "N/A")
    
    print(f"""
🗄️  PostgreSQL Database
├─ Type:     PostgreSQL
├─ Host:     {db_host}
├─ Port:     {db_port}
├─ Database: {db_name}
├─ User:     {db_user}
└─ Status:   ✅ Connected
""")

# ============================================================================
# FOOTER
# ============================================================================
print_separator()
print(f"\n✅ Log retrieval completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("\n" + "=" * 100)
