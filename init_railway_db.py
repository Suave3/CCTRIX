#!/usr/bin/env python3
"""
Railway Database Initialization with External Connection
Use this when connecting from outside Railway environment
"""

import psycopg2
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Get config from .env file
def get_db_config():
    return {
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": os.environ.get("DB_PORT", "5432"),
        "user": os.environ.get("DB_USER", "postgres"),
        "password": os.environ.get("DB_PASSWORD", ""),
        "database": os.environ.get("DB_NAME", "railway"),
    }

def init_railway_database():
    """Initialize database on Railway"""
    
    config = get_db_config()
    
    print("🚀 Connecting to Railway PostgreSQL...")
    print(f"   Host: {config['host']}")
    print(f"   Port: {config['port']}")
    print(f"   Database: {config['database']}")
    
    try:
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        print("✅ Connected to Railway!")
        
        # Create users table
        print("\n📝 Creating 'users' table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'viewer',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        print("✅ 'users' table created")
        
        # Create detection_logs table
        print("📝 Creating 'detection_logs' table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS detection_logs (
            id SERIAL PRIMARY KEY,
            person_detected BOOLEAN,
            confidence FLOAT,
            image_path TEXT,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        print("✅ 'detection_logs' table created")
        
        # Create auth_logs table
        print("📝 Creating 'auth_logs' table...")
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
        print("✅ 'auth_logs' table created")
        
        # Create failed_login_attempts table
        print("📝 Creating 'failed_login_attempts' table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS failed_login_attempts (
            id SERIAL PRIMARY KEY,
            username TEXT,
            ip_address TEXT,
            user_agent TEXT,
            attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        print("✅ 'failed_login_attempts' table created")
        
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
        
        print("✅ Indexes created")
        
        # Commit all changes
        conn.commit()
        
        # Verify tables
        print("\n📋 Verifying tables...")
        cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        for table, in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   ✓ {table:<30} {count:>5} rows")
        
        print("\n" + "="*60)
        print("✅ Railway Database Initialization COMPLETE!")
        print("="*60)
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"\n❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = init_railway_database()
    sys.exit(0 if success else 1)
