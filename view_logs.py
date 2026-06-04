#!/usr/bin/env python3
"""
CCTRIX Simple Log Viewer
Displays logs in a simple, readable format
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

try:
    import database as db
except Exception as e:
    print(f"❌ Failed to import database: {e}")
    sys.exit(1)

print("\n" + "=" * 100)
print("CCTRIX DATABASE LOGS".center(100))
print("=" * 100)

# Users
print("\n" + "█" * 100)
print("📋 REGISTERED USERS")
print("█" * 100)
users = db.execute_query("SELECT id, username, role, created_at FROM users", fetch=True)
if users:
    print(f"\nTotal Users: {len(users)}\n")
    for user in users:
        print(f"  ID: {user[0]}")
        print(f"  Username: {user[1]}")
        print(f"  Role: {user[2]}")
        print(f"  Created: {user[3]}")
        print()
else:
    print("  No users found\n")

# Failed Logins
print("\n" + "█" * 100)
print("⚠️  FAILED LOGIN ATTEMPTS")
print("█" * 100)
failed = db.execute_query("SELECT id, username, ip_address, user_agent, attempted_at FROM failed_login_attempts ORDER BY id DESC", fetch=True)
if failed:
    print(f"\nTotal Failed Attempts: {len(failed)}\n")
    for attempt in failed:
        print(f"  ID: {attempt[0]}")
        print(f"  Username: {attempt[1]}")
        print(f"  IP: {attempt[2]}")
        print(f"  User Agent: {attempt[3]}")
        print(f"  Time: {attempt[4]}")
        print()
else:
    print("  No failed login attempts found\n")

# Auth Logs
print("\n" + "█" * 100)
print("🔐 AUTHENTICATION LOGS")
print("█" * 100)
auth = db.execute_query("SELECT id, username, action, reason, ip_address, timestamp FROM auth_logs ORDER BY id DESC", fetch=True)
if auth:
    print(f"\nTotal Auth Events: {len(auth)}\n")
    for log in auth:
        print(f"  ID: {log[0]}")
        print(f"  User: {log[1]}")
        print(f"  Action: {log[2]}")
        print(f"  Reason: {log[3]}")
        print(f"  IP: {log[4]}")
        print(f"  Time: {log[5]}")
        print()
else:
    print("  No auth logs found\n")

# Detection Logs
print("\n" + "█" * 100)
print("🎥 DETECTION LOGS")
print("█" * 100)
detections = db.execute_query("SELECT id, person_detected, confidence, image_path, detected_at FROM detection_logs ORDER BY id DESC LIMIT 10", fetch=True)
if detections:
    total = db.execute_query("SELECT COUNT(*) FROM detection_logs", fetch=True)
    print(f"\nTotal Detections: {total[0][0]} (showing last 10)\n")
    for det in detections:
        detected_str = "✅ YES" if det[1] else "❌ NO"
        conf_str = f"{float(det[2]):.1%}" if det[2] else "N/A"
        print(f"  ID: {det[0]}")
        print(f"  Person Detected: {detected_str}")
        print(f"  Confidence: {conf_str}")
        print(f"  Image: {det[3]}")
        print(f"  Time: {det[4]}")
        print()
else:
    print("  No detection logs found\n")

# Summary
print("\n" + "=" * 100)
print("📊 SUMMARY".center(100))
print("=" * 100)
total_users = db.count_total_users()
total_detections = db.count_total_detections()
total_auth = db.count_total_auth_logs()
total_failed = db.count_total_failed_logins()
today_detections = db.count_detections_today()
today_auth = db.count_auth_logs_today()
today_failed = db.count_failed_logins_today()

print(f"""
Overall:
  • Users: {total_users}
  • Total Detections: {total_detections}
  • Total Auth Events: {total_auth}
  • Total Failed Logins: {total_failed}

Today:
  • Detections: {today_detections}
  • Auth Events: {today_auth}
  • Failed Logins: {today_failed}
""")

print("=" * 100 + "\n")
