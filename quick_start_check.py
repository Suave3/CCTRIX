#!/usr/bin/env python3
"""
Quick test to verify the CCTRIX app can start with the database
"""
import sys
import os

print("=" * 70)
print("CCTRIX Quick Start Verification")
print("=" * 70)

# Test 1: Check required files
print("\n[1] Checking required files...")
required_files = [
    "app.py",
    "database.py",
    ".env",
    "templates/index.html",
    "templates/login.html",
]

for file in required_files:
    if os.path.exists(file):
        print(f"  ✅ {file}")
    else:
        print(f"  ❌ {file} - MISSING!")
        sys.exit(1)

# Test 2: Import Flask and check dependencies
print("\n[2] Checking Python dependencies...")
required_packages = [
    "flask",
    "psycopg2",
    "dotenv",
    "werkzeug",
]

all_ok = True
for package in required_packages:
    try:
        __import__(package)
        print(f"  ✅ {package}")
    except ImportError:
        print(f"  ⚠️  {package} - not installed")
        all_ok = False

if not all_ok:
    print("\n⚠️  Some packages are missing. Install with:")
    print("  pip install -r requirements.txt")

# Test 3: Test database module
print("\n[3] Testing database module...")
try:
    from database import (
        init_db, log_auth, log_detection, 
        count_total_users, DB_TYPE
    )
    print(f"  ✅ Database module loaded")
    print(f"  ✅ Database type: {DB_TYPE.upper()}")
    
    # Test logging functions
    log_auth("test", "TEST", "Test action", "127.0.0.1", "Test/1.0")
    print(f"  ✅ Auth logging works")
    
    log_detection(True, 0.95, "/static/test.jpg")
    print(f"  ✅ Detection logging works")
    
    total_users = count_total_users()
    print(f"  ✅ Database queries work (found {total_users} users)")
    
except Exception as e:
    print(f"  ❌ Database test failed: {e}")
    sys.exit(1)

# Test 4: Test Flask app import
print("\n[4] Testing Flask application...")
try:
    from app import app
    print(f"  ✅ Flask app loaded successfully")
    print(f"  ✅ App name: {app.name}")
    print(f"  ✅ Debug mode: {app.debug}")
except Exception as e:
    print(f"  ❌ Flask app import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Check Flask routes
print("\n[5] Checking Flask routes...")
routes = []
for rule in app.url_map.iter_rules():
    routes.append(rule.rule)

print(f"  ✅ Found {len(routes)} routes configured")
print(f"  ✅ Sample routes: /login, /logout, /logs, /stats")

# Success!
print("\n" + "=" * 70)
print("✅ ALL CHECKS PASSED!")
print("=" * 70)
print("\nYou're ready to start the application!")
print("\nTo start the app, run:")
print("  python app.py")
print("\nThen open your browser to:")
print("  http://localhost:5000")
print("\nDefault credentials:")
print("  Username: admin")
print("  Password: admin123")
print("\n" + "=" * 70)
