#!/usr/bin/env python3
"""
Test script to verify PostgreSQL database connection and tables setup
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("PostgreSQL Database Connection Test")
print("=" * 60)

# Test 1: Check environment variables
print("\n[1] Checking environment variables...")
db_host = os.environ.get("DB_HOST")
db_port = os.environ.get("DB_PORT")
db_user = os.environ.get("DB_USER")
db_password = os.environ.get("DB_PASSWORD")
db_name = os.environ.get("DB_NAME")

print(f"  DB_HOST: {db_host}")
print(f"  DB_PORT: {db_port}")
print(f"  DB_USER: {db_user}")
print(f"  DB_PASSWORD: {'***' if db_password else 'NOT SET'}")
print(f"  DB_NAME: {db_name}")

if not all([db_host, db_port, db_user, db_password, db_name]):
    print("\n❌ ERROR: Missing required environment variables!")
    sys.exit(1)

print("✅ All environment variables set")

# Test 2: Import database module
print("\n[2] Importing database module...")
try:
    import database as db
    print("✅ Database module imported successfully")
except Exception as e:
    print(f"❌ Failed to import database module: {e}")
    sys.exit(1)

# Test 3: Initialize database
print("\n[3] Initializing database...")
try:
    if db.init_db():
        print("✅ Database initialized successfully")
    else:
        print("❌ Failed to initialize database")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error initializing database: {e}")
    sys.exit(1)

# Test 4: Test logging functions
print("\n[4] Testing logging functions...")
try:
    # Test auth log
    db.log_auth("test_user", "TEST_ACTION", "Testing database setup", "127.0.0.1", "Mozilla/5.0")
    print("  ✅ Auth logging works")
    
    # Test detection log
    db.log_detection(True, 0.95, "/static/test.jpg")
    print("  ✅ Detection logging works")
    
    # Test failed login log
    db.log_failed_login("test_user", "127.0.0.1", "Mozilla/5.0")
    print("  ✅ Failed login logging works")
    
except Exception as e:
    print(f"  ❌ Logging test failed: {e}")
    sys.exit(1)

# Test 5: Verify data retrieval
print("\n[5] Verifying data retrieval...")
try:
    auth_logs = db.get_recent_auth_logs(5)
    print(f"  ✅ Retrieved {len(auth_logs) if auth_logs else 0} auth logs")
    
    detection_logs = db.get_recent_detections(5)
    print(f"  ✅ Retrieved {len(detection_logs) if detection_logs else 0} detection logs")
    
    failed_logins = db.get_recent_failed_logins(5)
    print(f"  ✅ Retrieved {len(failed_logins) if failed_logins else 0} failed login records")
    
except Exception as e:
    print(f"  ❌ Data retrieval test failed: {e}")
    sys.exit(1)

# Test 6: Check table counts
print("\n[6] Checking table record counts...")
try:
    total_detections = db.count_total_detections()
    total_auth = db.count_total_auth_logs()
    total_users = db.count_total_users()
    total_failed = db.count_total_failed_logins()
    
    print(f"  Detection logs: {total_detections} records")
    print(f"  Auth logs: {total_auth} records")
    print(f"  Users: {total_users} records")
    print(f"  Failed logins: {total_failed} records")
    print("  ✅ Table counts retrieved successfully")
    
except Exception as e:
    print(f"  ❌ Table count test failed: {e}")
    sys.exit(1)

# Summary
print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED!")
print("=" * 60)
print("\nYour PostgreSQL database is now ready to use!")
print("You can start the Flask application with: python app.py")
print("=" * 60)
