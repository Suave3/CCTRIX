#!/usr/bin/env python3
"""
Check which databases exist and their connections
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

print("🔍 DATABASE CONNECTION INVESTIGATION")
print("="*70)

# Get config
config_external = {
    "host": "turntable.proxy.rlwy.net",
    "port": "43684",
    "user": "postgres",
    "password": os.environ.get("DB_PASSWORD"),
    "database": "railway",
}

config_internal = {
    "host": "postgres.railway.internal",
    "port": "5432",
    "user": "postgres",
    "password": os.environ.get("DB_PASSWORD"),
    "database": "railway",
}

config_env = {
    "host": os.environ.get("DB_HOST"),
    "port": os.environ.get("DB_PORT"),
    "user": os.environ.get("DB_USER"),
    "password": os.environ.get("DB_PASSWORD"),
    "database": os.environ.get("DB_NAME"),
}

# Test external connection
print("\n1️⃣  EXTERNAL CONNECTION (turntable.proxy.rlwy.net:43684)")
print("-" * 70)
try:
    conn = psycopg2.connect(**config_external)
    cursor = conn.cursor()
    
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    print(f"   ✅ CONNECTED")
    print(f"   Version: {version.split(',')[0]}")
    
    cursor.execute("""
    SELECT table_name FROM information_schema.tables 
    WHERE table_schema = 'public'
    ORDER BY table_name
    """)
    
    tables = cursor.fetchall()
    print(f"   Tables: {len(tables)}")
    for table, in tables:
        print(f"      • {table}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"   ❌ FAILED: {e}")

# Test internal connection
print("\n2️⃣  INTERNAL CONNECTION (postgres.railway.internal:5432)")
print("-" * 70)
try:
    conn = psycopg2.connect(**config_internal)
    cursor = conn.cursor()
    
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    print(f"   ✅ CONNECTED")
    print(f"   Version: {version.split(',')[0]}")
    
    cursor.execute("""
    SELECT table_name FROM information_schema.tables 
    WHERE table_schema = 'public'
    ORDER BY table_name
    """)
    
    tables = cursor.fetchall()
    print(f"   Tables: {len(tables)}")
    for table, in tables:
        print(f"      • {table}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"   ❌ FAILED: {e}")

# Test .env config
print("\n3️⃣  CURRENT .ENV CONFIG")
print("-" * 70)
print(f"   Host: {config_env['host']}")
print(f"   Port: {config_env['port']}")
print(f"   Database: {config_env['database']}")

try:
    conn = psycopg2.connect(**config_env)
    cursor = conn.cursor()
    
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    print(f"   ✅ CONNECTED")
    print(f"   Version: {version.split(',')[0]}")
    
    cursor.execute("""
    SELECT table_name FROM information_schema.tables 
    WHERE table_schema = 'public'
    ORDER BY table_name
    """)
    
    tables = cursor.fetchall()
    print(f"   Tables: {len(tables)}")
    for table, in tables:
        print(f"      • {table}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"   ❌ FAILED: {e}")

print("\n" + "="*70)
print("DIAGNOSIS:")
print("="*70)
print("""
If External and Internal have DIFFERENT tables counts:
  → There are TWO different databases!
  → Railway app uses INTERNAL (postgres.railway.internal)
  → We need to create tables in the INTERNAL one

If External has tables but Internal doesn't:
  → We're connected to the WRONG database in .env
  → Need to use postgres.railway.internal in production
""")
