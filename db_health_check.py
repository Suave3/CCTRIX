#!/usr/bin/env python3
"""
Comprehensive Database Verification & Setup Tool
Verifies and fixes any database issues
"""

import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def get_db_config():
    return {
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": os.environ.get("DB_PORT", "5432"),
        "user": os.environ.get("DB_USER", "postgres"),
        "password": os.environ.get("DB_PASSWORD", ""),
        "database": os.environ.get("DB_NAME", "railway"),
    }

def full_database_health_check():
    """Complete database health check"""
    config = get_db_config()
    
    print("\n" + "="*70)
    print("🔍 COMPLETE DATABASE HEALTH CHECK")
    print("="*70)
    
    print(f"\n📡 Connection Details:")
    print(f"   Host: {config['host']}")
    print(f"   Port: {config['port']}")
    print(f"   Database: {config['database']}")
    print(f"   User: {config['user']}")
    
    try:
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        print("\n✅ Database connection: SUCCESS")
        
        # Check PostgreSQL version
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"   PostgreSQL: {version.split(',')[0]}")
        
        # 1. Check all tables exist
        print("\n📋 TABLE CHECK:")
        required_tables = ['users', 'detection_logs', 'auth_logs', 'failed_login_attempts']
        
        cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
        """)
        
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        for table in required_tables:
            if table in existing_tables:
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   ✅ {table:<30} {count:>5} rows")
            else:
                print(f"   ❌ {table:<30} MISSING")
        
        # 2. Check indexes
        print("\n🔑 INDEX CHECK:")
        cursor.execute("""
        SELECT indexname 
        FROM pg_indexes 
        WHERE schemaname = 'public'
        ORDER BY indexname
        """)
        
        indexes = cursor.fetchall()
        if indexes:
            for idx, in indexes:
                print(f"   ✅ {idx}")
        else:
            print("   ⚠️  No indexes found")
        
        # 3. Check constraints
        print("\n🔒 CONSTRAINT CHECK:")
        cursor.execute("""
        SELECT constraint_name, constraint_type 
        FROM information_schema.table_constraints 
        WHERE table_schema = 'public'
        ORDER BY constraint_name
        """)
        
        constraints = cursor.fetchall()
        for const_name, const_type in constraints:
            print(f"   ✅ {const_name:<35} ({const_type})")
        
        # 4. Check data integrity
        print("\n📊 DATA INTEGRITY CHECK:")
        
        # Users check
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"   Users: {user_count} record(s)")
        
        if user_count > 0:
            cursor.execute("""
            SELECT username, role, created_at 
            FROM users 
            ORDER BY created_at
            """)
            for username, role, created_at in cursor.fetchall():
                print(f"      • {username} ({role}) - {created_at}")
        
        # Detection logs
        cursor.execute("""
        SELECT COUNT(*), 
               SUM(CASE WHEN person_detected THEN 1 ELSE 0 END),
               ROUND(AVG(confidence)::numeric, 3),
               MAX(detected_at),
               MIN(detected_at)
        FROM detection_logs
        """)
        
        total, detected, avg_conf, latest, oldest = cursor.fetchone()
        print(f"\n   Detection Logs: {total} record(s)")
        if total > 0:
            print(f"      • Persons detected: {detected}")
            print(f"      • Avg confidence: {avg_conf}")
            print(f"      • Latest: {latest}")
            print(f"      • Oldest: {oldest}")
        
        # Auth logs
        cursor.execute("""
        SELECT action, COUNT(*) 
        FROM auth_logs 
        GROUP BY action 
        ORDER BY COUNT(*) DESC
        """)
        
        print(f"\n   Auth Logs Summary:")
        auth_actions = cursor.fetchall()
        if auth_actions:
            for action, count in auth_actions:
                print(f"      • {action}: {count}")
        else:
            print("      (no records)")
        
        # Failed attempts
        cursor.execute("""
        SELECT COUNT(*), 
               COUNT(DISTINCT username),
               COUNT(DISTINCT ip_address),
               MAX(attempted_at)
        FROM failed_login_attempts
        """)
        
        total_failed, unique_users, unique_ips, latest_attempt = cursor.fetchone()
        print(f"\n   Failed Login Attempts: {total_failed} record(s)")
        if total_failed > 0:
            print(f"      • Unique users: {unique_users}")
            print(f"      • Unique IPs: {unique_ips}")
            print(f"      • Latest: {latest_attempt}")
        
        # 5. Database size
        print("\n💾 DATABASE SIZE:")
        cursor.execute("""
        SELECT 
            pg_size_pretty(pg_database_size(current_database())) as size
        """)
        
        size = cursor.fetchone()[0]
        print(f"   Total size: {size}")
        
        # 6. Overall status
        print("\n" + "="*70)
        if len(existing_tables) == len(required_tables):
            print("✅ DATABASE STATUS: FULLY OPERATIONAL")
        else:
            print("⚠️  DATABASE STATUS: NEEDS REPAIR")
        print("="*70 + "\n")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"\n❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

def repair_database():
    """Repair/recreate all database tables"""
    config = get_db_config()
    
    print("\n🔧 REPAIRING DATABASE...")
    
    try:
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        
        # Drop existing tables (careful!)
        tables = ['detection_logs', 'failed_login_attempts', 'auth_logs', 'users']
        for table in tables:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                print(f"   Dropped: {table}")
            except:
                pass
        
        conn.commit()
        
        # Recreate tables
        print("\n   Creating tables...")
        
        cursor.execute("""
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'viewer',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        cursor.execute("""
        CREATE TABLE detection_logs (
            id SERIAL PRIMARY KEY,
            person_detected BOOLEAN,
            confidence FLOAT,
            image_path TEXT,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        cursor.execute("""
        CREATE TABLE auth_logs (
            id SERIAL PRIMARY KEY,
            username TEXT,
            action TEXT,
            reason TEXT,
            ip_address TEXT,
            user_agent TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        cursor.execute("""
        CREATE TABLE failed_login_attempts (
            id SERIAL PRIMARY KEY,
            username TEXT,
            ip_address TEXT,
            user_agent TEXT,
            attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create indexes
        print("   Creating indexes...")
        
        cursor.execute("""
        CREATE INDEX idx_detection_logs_detected_at 
        ON detection_logs(detected_at DESC)
        """)
        
        cursor.execute("""
        CREATE INDEX idx_auth_logs_timestamp 
        ON auth_logs(timestamp DESC)
        """)
        
        cursor.execute("""
        CREATE INDEX idx_auth_logs_username 
        ON auth_logs(username)
        """)
        
        cursor.execute("""
        CREATE INDEX idx_failed_login_username 
        ON failed_login_attempts(username)
        """)
        
        cursor.execute("""
        CREATE INDEX idx_failed_login_attempted_at 
        ON failed_login_attempts(attempted_at DESC)
        """)
        
        cursor.execute("""
        CREATE INDEX idx_users_username 
        ON users(username)
        """)
        
        conn.commit()
        print("\n✅ Database repair complete!")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Repair failed: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "repair":
        repair_database()
    else:
        full_database_health_check()
