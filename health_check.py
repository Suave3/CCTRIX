#!/usr/bin/env python3
"""
Deployment Health Check
Verifies app can start and connect to database
"""

import os
import sys
from dotenv import load_dotenv

print("🔍 DEPLOYMENT HEALTH CHECK")
print("="*60)

load_dotenv()

# 1. Check environment variables
print("\n1️⃣  ENVIRONMENT VARIABLES:")
required_vars = ['DB_HOST', 'DB_PORT', 'DB_USER', 'DB_PASSWORD', 'DB_NAME', 'SECRET_KEY']

for var in required_vars:
    value = os.environ.get(var, "")
    if value:
        masked = value[:5] + "***" if len(value) > 5 else "***"
        print(f"   ✅ {var:<20} {masked}")
    else:
        print(f"   ❌ {var:<20} MISSING!")

# 2. Check Python imports
print("\n2️⃣  PYTHON IMPORTS:")
required_imports = [
    ('flask', 'Flask'),
    ('psycopg2', 'PostgreSQL'),
    ('numpy', 'NumPy'),
    ('dotenv', 'Python-dotenv'),
    ('werkzeug', 'Werkzeug'),
    ('gunicorn', 'Gunicorn'),
]

for module, name in required_imports:
    try:
        __import__(module)
        print(f"   ✅ {name:<20} installed")
    except ImportError:
        print(f"   ❌ {name:<20} MISSING!")

# 3. Test database connection
print("\n3️⃣  DATABASE CONNECTION:")
try:
    import psycopg2
    
    config = {
        "host": os.environ.get("DB_HOST"),
        "port": os.environ.get("DB_PORT"),
        "user": os.environ.get("DB_USER"),
        "password": os.environ.get("DB_PASSWORD"),
        "database": os.environ.get("DB_NAME"),
    }
    
    if all(config.values()):
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public'
        """)
        
        tables = len(cursor.fetchall())
        print(f"   ✅ Connected! Found {tables} tables")
        
        cursor.close()
        conn.close()
    else:
        print("   ❌ Missing database configuration")
        
except Exception as e:
    print(f"   ❌ Connection failed: {e}")

# 4. Test Flask app import
print("\n4️⃣  FLASK APP IMPORT:")
try:
    # Try importing the app
    sys.path.insert(0, '/app' if os.path.exists('/app') else '.')
    
    from app import app
    print(f"   ✅ App imported successfully")
    print(f"   ✅ App debug mode: {app.debug}")
    
except Exception as e:
    print(f"   ❌ App import failed: {e}")
    import traceback
    print("\n   Stack trace:")
    print("   " + "\n   ".join(traceback.format_exc().split("\n")))

print("\n" + "="*60)
print("✅ Health check complete!")
