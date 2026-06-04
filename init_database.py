#!/usr/bin/env python3
"""
Database Initialization Script for cctrix (CCTV System)
Initializes all required tables and indexes
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_config():
    return {
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": os.environ.get("DB_PORT", "5432"),
        "user": os.environ.get("DB_USER", "postgres"),
        "password": os.environ.get("DB_PASSWORD", ""),
        "database": os.environ.get("DB_NAME", "railway"),
    }

def init_database():
    """Initialize all database tables and indexes"""
    
    config = get_db_config()
    print(f"🔄 Connecting to database: {config['database']} at {config['host']}:{config['port']}")
    
    try:
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        print("✅ Connected to database")
        
        # Table 1: Users
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
        
        # Table 2: Detection Logs
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
        
        # Table 3: Auth Logs
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
        
        # Table 4: Failed Login Attempts
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
        
        # Create Indexes for Better Performance
        print("\n📊 Creating indexes for performance...")
        
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
        
        conn.commit()
        
        # Display table info
        print("\n📋 Database Tables Summary:")
        cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        for table in tables:
            print(f"  ✓ {table[0]}")
        
        print("\n✅ Database initialization complete!")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = init_database()
    exit(0 if success else 1)
