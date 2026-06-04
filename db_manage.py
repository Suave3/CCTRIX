#!/usr/bin/env python3
"""
Database Management Utilities for cctrix
View stats, backup schema, and manage data
"""

import psycopg2
import os
import json
from datetime import datetime
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

def db_stats():
    """Show database statistics"""
    config = get_db_config()
    
    try:
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        
        print("\n" + "="*60)
        print("📊 DATABASE STATISTICS")
        print("="*60)
        
        tables = {
            'users': 'SELECT COUNT(*) as count FROM users',
            'detection_logs': 'SELECT COUNT(*) as count FROM detection_logs',
            'auth_logs': 'SELECT COUNT(*) as count FROM auth_logs',
            'failed_login_attempts': 'SELECT COUNT(*) as count FROM failed_login_attempts'
        }
        
        for table_name, query in tables.items():
            cursor.execute(query)
            count = cursor.fetchone()[0]
            print(f"  {table_name:.<30} {count:>5} rows")
        
        # Latest detection
        cursor.execute("""
        SELECT COUNT(*) as total, 
               SUM(CASE WHEN person_detected THEN 1 ELSE 0 END) as detected,
               ROUND(AVG(confidence)::numeric, 3) as avg_confidence
        FROM detection_logs
        """)
        
        row = cursor.fetchone()
        print(f"\n  📷 Detection Stats:")
        print(f"    Total detections: {row[0]}")
        print(f"    Persons detected: {row[1] or 0}")
        if row[2]:
            print(f"    Avg confidence: {row[2]}")
        
        # Latest auth activity
        cursor.execute("""
        SELECT action, COUNT(*) as count 
        FROM auth_logs 
        GROUP BY action 
        ORDER BY count DESC
        """)
        
        print(f"\n  🔐 Recent Auth Activity:")
        for action, count in cursor.fetchall():
            print(f"    {action}: {count}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def create_admin_user(username, password):
    """Create admin user"""
    config = get_db_config()
    
    try:
        from werkzeug.security import generate_password_hash
        
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        
        password_hash = generate_password_hash(password)
        
        cursor.execute("""
        INSERT INTO users (username, password_hash, role)
        VALUES (%s, %s, 'admin')
        ON CONFLICT (username) DO UPDATE
        SET password_hash = EXCLUDED.password_hash, role = 'admin'
        """, (username, password_hash))
        
        conn.commit()
        print(f"✅ Admin user '{username}' created/updated!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def clear_old_logs(days=30):
    """Clear logs older than N days"""
    config = get_db_config()
    
    try:
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        
        cursor.execute("""
        DELETE FROM auth_logs 
        WHERE timestamp < NOW() - INTERVAL '%s days'
        """, (days,))
        
        auth_deleted = cursor.rowcount
        
        cursor.execute("""
        DELETE FROM detection_logs 
        WHERE detected_at < NOW() - INTERVAL '%s days'
        """, (days,))
        
        detection_deleted = cursor.rowcount
        
        conn.commit()
        
        print(f"✅ Cleaned up old logs:")
        print(f"  Auth logs deleted: {auth_deleted}")
        print(f"  Detection logs deleted: {detection_deleted}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def export_schema():
    """Export database schema to file"""
    config = get_db_config()
    
    try:
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        
        schema = {
            'timestamp': datetime.now().isoformat(),
            'tables': {}
        }
        
        cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
        """)
        
        for table_name, in cursor.fetchall():
            cursor.execute(f"""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position
            """)
            
            columns = []
            for col_name, data_type, nullable in cursor.fetchall():
                columns.append({
                    'name': col_name,
                    'type': data_type,
                    'nullable': nullable == 'YES'
                })
            
            schema['tables'][table_name] = {'columns': columns}
        
        filepath = 'database_schema.json'
        with open(filepath, 'w') as f:
            json.dump(schema, f, indent=2)
        
        print(f"✅ Schema exported to {filepath}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "stats":
            db_stats()
        elif command == "admin":
            if len(sys.argv) < 4:
                print("Usage: python db_manage.py admin <username> <password>")
                sys.exit(1)
            create_admin_user(sys.argv[2], sys.argv[3])
        elif command == "cleanup":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            clear_old_logs(days)
        elif command == "export":
            export_schema()
        else:
            print("❌ Unknown command")
    else:
        print("""
Available commands:
  stats              - Show database statistics
  admin <user> <pwd> - Create admin user
  cleanup [days]     - Remove logs older than N days (default 30)
  export             - Export schema to JSON
        """)
