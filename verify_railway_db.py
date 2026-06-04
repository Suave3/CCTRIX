#!/usr/bin/env python3
"""
Verify what's actually in Railway database
Shows exact table status and schema
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def check_railway_database():
    """Check what's actually in the Railway database"""
    
    config = {
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": os.environ.get("DB_PORT", "5432"),
        "user": os.environ.get("DB_USER", "postgres"),
        "password": os.environ.get("DB_PASSWORD", ""),
        "database": os.environ.get("DB_NAME", "railway"),
    }
    
    print("🔍 Checking Railway Database...")
    print(f"   Connection: {config['host']}:{config['port']}/{config['database']}")
    
    try:
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        print("✅ Connected!\n")
        
        # Check all tables in all schemas
        print("📊 ALL TABLES IN DATABASE:")
        cursor.execute("""
        SELECT table_schema, table_name, table_type
        FROM information_schema.tables
        ORDER BY table_schema, table_name
        """)
        
        tables = cursor.fetchall()
        
        if not tables:
            print("   ❌ NO TABLES FOUND!")
        else:
            for schema, table_name, table_type in tables:
                print(f"   {schema}.{table_name} ({table_type})")
                
                # Get row count for public schema tables
                if schema == 'public':
                    cursor.execute(f"SELECT COUNT(*) FROM {schema}.{table_name}")
                    count = cursor.fetchone()[0]
                    print(f"      └─ {count} rows")
        
        # Check schemas
        print("\n📁 ALL SCHEMAS:")
        cursor.execute("""
        SELECT schema_name 
        FROM information_schema.schemata
        ORDER BY schema_name
        """)
        
        for schema, in cursor.fetchall():
            print(f"   • {schema}")
        
        # Check public schema specifically
        print("\n🔎 PUBLIC SCHEMA TABLES:")
        cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
        """)
        
        public_tables = cursor.fetchall()
        if not public_tables:
            print("   ❌ NO TABLES IN PUBLIC SCHEMA")
        else:
            for table, in public_tables:
                print(f"   ✓ {table}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_railway_database()
