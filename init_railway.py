#!/usr/bin/env python3
"""
Railway Deployment Initialization Hook
This runs ONCE when the app starts on Railway
Creates all tables in the Railway PostgreSQL database
Auto-detects DATABASE_URL environment variable
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv
from urllib.parse import urlparse
import time

load_dotenv()

def init_railway_database():
    """Initialize database on Railway startup"""
    
    # Try to parse DATABASE_URL first (Railway auto-sets this)
    db_url = os.environ.get("DATABASE_URL")
    
    if db_url:
        # Parse DATABASE_URL
        url = urlparse(db_url)
        config = {
            "host": url.hostname,
            "port": url.port or 5432,
            "user": url.username,
            "password": url.password,
            "database": url.path.lstrip("/"),
            "connect_timeout": 10,
            "sslmode": "require",  # Railway requires SSL
        }
        print("✅ Using DATABASE_URL (Railway PostgreSQL)")
    else:
        # Fall back to individual environment variables
        config = {
            "host": os.environ.get("DB_HOST"),
            "port": int(os.environ.get("DB_PORT", "5432")),
            "user": os.environ.get("DB_USER"),
            "password": os.environ.get("DB_PASSWORD"),
            "database": os.environ.get("DB_NAME"),
        }
        print("ℹ️  Using individual DB_* environment variables")
    
    print("\n" + "="*70)
    print("🚀 RAILWAY DATABASE INITIALIZATION")
    print("="*70)
    print(f"   Host: {config['host']}")
    print(f"   Database: {config['database']}")
    
    # Retry connection a few times in case database is starting
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            conn = psycopg2.connect(**config)
            cursor = conn.cursor()
            print("✅ Connected to Railway PostgreSQL!")
            break
        except psycopg2.Error as e:
            retry_count += 1
            if retry_count < max_retries:
                print(f"   ⏳ Connection attempt {retry_count}/{max_retries} failed, retrying in 2s...")
                time.sleep(2)
            else:
                print(f"❌ Failed to connect after {max_retries} attempts")
                return False
    
    try:
        # Create all tables
        print("\n📝 Creating tables...")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'viewer',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        print("   ✓ users")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS detection_logs (
            id SERIAL PRIMARY KEY,
            person_detected BOOLEAN,
            confidence FLOAT,
            image_path TEXT,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        print("   ✓ detection_logs")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS auth_logs (
            id SERIAL PRIMARY KEY,
            username TEXT,
            action TEXT,
            reason TEXT,
            ip_address TEXT,
            user_agent TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        print("   ✓ auth_logs")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS failed_login_attempts (
            id SERIAL PRIMARY KEY,
            username TEXT,
            ip_address TEXT,
            user_agent TEXT,
            attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        print("   ✓ failed_login_attempts")
        
        # Create indexes
        print("\n📊 Creating indexes...")
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_detection_logs_detected_at 
        ON detection_logs(detected_at DESC)
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_auth_logs_timestamp 
        ON auth_logs(timestamp DESC)
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_auth_logs_username 
        ON auth_logs(username)
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_failed_login_username 
        ON failed_login_attempts(username)
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_failed_login_attempted_at 
        ON failed_login_attempts(attempted_at DESC)
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_username 
        ON users(username)
        """)
        
        print("   ✓ All indexes")
        
        conn.commit()
        
        # Verify
        print("\n✅ Verifying tables...")
        cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
        """)
        
        for table, in cursor.fetchall():
            print(f"   ✓ {table}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*70)
        print("✅ DATABASE INITIALIZATION COMPLETE!")
        print("="*70 + "\n")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = init_railway_database()
    sys.exit(0 if success else 1)
