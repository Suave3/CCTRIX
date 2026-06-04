#!/usr/bin/env python3
"""Test Railway PostgreSQL database connection"""

import psycopg2
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def test_connection():
    """Test database connection"""
    
    db_config = {
        "host": os.environ.get("DB_HOST"),
        "port": os.environ.get("DB_PORT"),
        "user": os.environ.get("DB_USER"),
        "password": os.environ.get("DB_PASSWORD"),
        "database": os.environ.get("DB_NAME"),
    }
    
    print("=" * 60)
    print("Testing Railway PostgreSQL Connection")
    print("=" * 60)
    print(f"\nConnection Details:")
    print(f"  Host: {db_config['host']}")
    print(f"  Port: {db_config['port']}")
    print(f"  User: {db_config['user']}")
    print(f"  Database: {db_config['database']}")
    print(f"  Password: {'*' * len(db_config['password'])}")
    
    try:
        print("\n⏳ Attempting connection...")
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        print("✅ Connection SUCCESSFUL!")
        
        # Get server version
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"\n📊 PostgreSQL Version:")
        print(f"  {version[0]}")
        
        # List existing tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        
        if tables:
            print(f"\n📋 Existing Tables ({len(tables)}):")
            for table in tables:
                print(f"  • {table[0]}")
        else:
            print(f"\n📋 No tables found (database is empty)")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ Database is ready for deployment!")
        print("=" * 60)
        
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ Connection FAILED!")
        print(f"Error: {str(e)}")
        print("\n⚠️  Troubleshooting:")
        print("  1. Verify credentials in .env file")
        print("  2. Check if Railway PostgreSQL is running")
        print("  3. Ensure your IP is whitelisted in Railway (if applicable)")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_connection()
    exit(0 if success else 1)
