#!/usr/bin/env python3
"""
Database Setup Helper for CCTRIX
Choose between SQLite (local dev) or PostgreSQL (production)
"""
import os
import sys
from pathlib import Path

print("=" * 70)
print("CCTRIX Database Setup Helper")
print("=" * 70)

print("\nChoose your database setup:\n")
print("1. SQLite (Recommended for local development - no installation needed)")
print("2. PostgreSQL (Recommended for production)")
print("3. Remote PostgreSQL (Railway/Neon/Supabase)")

choice = input("\nEnter your choice (1-3): ").strip()

env_path = Path(".env")
env_example = Path(".env.example")

if choice == "1":
    print("\n" + "=" * 70)
    print("Setting up SQLite (Local Development)")
    print("=" * 70)
    
    env_content = """# Flask
SECRET_KEY=change_this_to_a_long_random_string_like_this_ReplaceMeWithYourOwn

# SQLite Configuration (No setup required!)
DB_TYPE=sqlite
DB_PATH=./cctrix.db

# Camera: 0 = webcam, or RTSP URL, or "screen" for screen capture
CAMERA_SOURCE=0

# Google reCAPTCHA v2 — official test keys for local development
RECAPTCHA_SITE_KEY=6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI
RECAPTCHA_SECRET_KEY=6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ17ZFtSe
"""
    
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print("\n✅ .env file configured for SQLite")
    print("\nTo start your application:")
    print("  python app.py")
    print("\nDatabase file will be created at: ./cctrix.db")
    print("\n✅ No additional setup needed! Just run the app.")

elif choice == "2":
    print("\n" + "=" * 70)
    print("Setting up PostgreSQL (Production)")
    print("=" * 70)
    
    print("\nPostgreSQL Setup Instructions:")
    print("\n1. Install PostgreSQL from: https://www.postgresql.org/download/windows/")
    print("   - Remember the password you set for 'postgres' user")
    print("   - Use default port 5432")
    print("\n2. Create database: createdb -U postgres cctrix_db")
    print("\n3. Update your .env file with:")
    
    db_host = input("\n   DB_HOST (default=localhost): ").strip() or "localhost"
    db_port = input("   DB_PORT (default=5432): ").strip() or "5432"
    db_user = input("   DB_USER (default=postgres): ").strip() or "postgres"
    db_password = input("   DB_PASSWORD: ").strip()
    db_name = input("   DB_NAME (default=cctrix_db): ").strip() or "cctrix_db"
    
    env_content = f"""# Flask
SECRET_KEY=change_this_to_a_long_random_string_like_this_ReplaceMeWithYourOwn

# PostgreSQL Configuration
DB_HOST={db_host}
DB_PORT={db_port}
DB_USER={db_user}
DB_PASSWORD={db_password}
DB_NAME={db_name}
DB_CONNECT_TIMEOUT=5

# Camera: 0 = webcam, or RTSP URL, or "screen" for screen capture
CAMERA_SOURCE=0

# Google reCAPTCHA v2 — official test keys for local development
RECAPTCHA_SITE_KEY=6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI
RECAPTCHA_SECRET_KEY=6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ17ZFtSe
"""
    
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print("\n✅ .env file configured for PostgreSQL")
    print("\nTo test your connection:")
    print("  python test_db_setup.py")

elif choice == "3":
    print("\n" + "=" * 70)
    print("Setting up Remote PostgreSQL")
    print("=" * 70)
    
    print("\nChoose your service:")
    print("1. Railway - https://railway.app")
    print("2. Neon - https://neon.tech")
    print("3. Supabase - https://supabase.com")
    
    service = input("\nEnter choice (1-3): ").strip()
    
    if service in ["1", "2", "3"]:
        print("\nGet your connection details from your service dashboard and enter them:")
        db_host = input("DB_HOST: ").strip()
        db_port = input("DB_PORT (default=5432): ").strip() or "5432"
        db_user = input("DB_USER: ").strip()
        db_password = input("DB_PASSWORD: ").strip()
        db_name = input("DB_NAME: ").strip()
        
        env_content = f"""# Flask
SECRET_KEY=change_this_to_a_long_random_string_like_this_ReplaceMeWithYourOwn

# PostgreSQL Configuration (Remote)
DB_HOST={db_host}
DB_PORT={db_port}
DB_USER={db_user}
DB_PASSWORD={db_password}
DB_NAME={db_name}
DB_CONNECT_TIMEOUT=10

# Camera: 0 = webcam, or RTSP URL, or "screen" for screen capture
CAMERA_SOURCE=0

# Google reCAPTCHA v2 — official test keys for local development
RECAPTCHA_SITE_KEY=6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI
RECAPTCHA_SECRET_KEY=6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ17ZFtSe
"""
        
        with open(env_path, 'w') as f:
            f.write(env_content)
        
        print("\n✅ .env file configured for remote PostgreSQL")
        print("\nTo test your connection:")
        print("  python test_db_setup.py")
    else:
        print("Invalid choice")
        sys.exit(1)

else:
    print("Invalid choice")
    sys.exit(1)

print("\n" + "=" * 70)
print("Next Steps:")
print("=" * 70)
print("\n1. Run the test script (if using PostgreSQL):")
print("   python test_db_setup.py")
print("\n2. Start your Flask application:")
print("   python app.py")
print("\n3. Open browser and navigate to:")
print("   http://localhost:5000")
print("\n4. Login with default credentials:")
print("   Username: admin")
print("   Password: admin123")
print("\n" + "=" * 70)
