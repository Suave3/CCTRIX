#!/usr/bin/env python3
"""
PostgreSQL Connection String Parser
Helps you use the Postgres.DATABASE_URL from Railway or other services
"""

import os
import sys
from urllib.parse import urlparse
from dotenv import load_dotenv

print("\n" + "=" * 80)
print("PostgreSQL Connection String Parser".center(80))
print("=" * 80)

print("""
Found a PostgreSQL connection string? Usually looks like:
  postgresql://user:password@host:port/database
  postgres://user:password@host:port/database

Or from Railway:
  ${{ Postgres.DATABASE_URL }}

This tool will help you parse it and configure your .env file.
""")

# Option 1: Parse from input
print("\n[Option 1] Paste your connection string here:")
print("(Or press Enter to skip and try Option 2)\n")

connection_string = input("Connection string: ").strip()

if connection_string and connection_string.startswith(("postgresql://", "postgres://")):
    print("\n✅ Parsing connection string...\n")
    
    try:
        parsed = urlparse(connection_string)
        
        db_user = parsed.username
        db_password = parsed.password
        db_host = parsed.hostname
        db_port = parsed.port or 5432
        db_name = parsed.path.lstrip('/')
        
        print(f"Extracted configuration:")
        print(f"  Host: {db_host}")
        print(f"  Port: {db_port}")
        print(f"  User: {db_user}")
        print(f"  Password: {'*' * len(db_password) if db_password else 'N/A'}")
        print(f"  Database: {db_name}")
        
        # Save to .env
        print("\nWould you like to save this to .env? (y/n): ", end="")
        if input().strip().lower() == 'y':
            with open(".env", "w") as f:
                f.write(f"""# Flask
SECRET_KEY=change_this_to_a_long_random_string_like_this_ReplaceMeWithYourOwn

# PostgreSQL Configuration (Railway/Cloud)
DB_TYPE=postgresql
DB_HOST={db_host}
DB_PORT={db_port}
DB_USER={db_user}
DB_PASSWORD={db_password}
DB_NAME={db_name}
DB_CONNECT_TIMEOUT=10

# Camera: 0 = webcam, or RTSP URL, or "screen" for screen capture
CAMERA_SOURCE=0

# Google reCAPTCHA v2 - official test keys for local development
RECAPTCHA_SITE_KEY=6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI
RECAPTCHA_SECRET_KEY=6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ17ZFtSe
""")
            print("✅ Configuration saved to .env")
            print("\nTo verify connection, run:")
            print("  python test_db_setup.py")
        else:
            print("Skipped saving to .env")
    except Exception as e:
        print(f"❌ Error parsing connection string: {e}")

# Option 2: Manual entry
elif not connection_string:
    print("\n[Option 2] Manual configuration entry\n")
    
    print("Enter your PostgreSQL connection details:")
    db_host = input("Host (e.g., postgres.railway.internal): ").strip()
    db_port = input("Port (default 5432): ").strip() or "5432"
    db_user = input("Username (e.g., postgres): ").strip()
    db_password = input("Password: ").strip()
    db_name = input("Database name: ").strip()
    
    print(f"\nConfiguration:")
    print(f"  Host: {db_host}")
    print(f"  Port: {db_port}")
    print(f"  User: {db_user}")
    print(f"  Password: {'*' * len(db_password) if db_password else 'N/A'}")
    print(f"  Database: {db_name}")
    
    print("\nSave to .env? (y/n): ", end="")
    if input().strip().lower() == 'y':
        with open(".env", "w") as f:
            f.write(f"""# Flask
SECRET_KEY=change_this_to_a_long_random_string_like_this_ReplaceMeWithYourOwn

# PostgreSQL Configuration
DB_TYPE=postgresql
DB_HOST={db_host}
DB_PORT={db_port}
DB_USER={db_user}
DB_PASSWORD={db_password}
DB_NAME={db_name}
DB_CONNECT_TIMEOUT=10

# Camera: 0 = webcam, or RTSP URL, or "screen" for screen capture
CAMERA_SOURCE=0

# Google reCAPTCHA v2 - official test keys for local development
RECAPTCHA_SITE_KEY=6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI
RECAPTCHA_SECRET_KEY=6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ17ZFtSe
""")
        print("✅ Configuration saved to .env")
        print("\nTo verify connection, run:")
        print("  python test_db_setup.py")
    else:
        print("Skipped saving to .env")

print("\n" + "=" * 80)
print("\n✅ Done!\n")
