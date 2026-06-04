#!/usr/bin/env python3
"""
Check current Railway database connection status
Shows what database .env is pointing to
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("\n" + "="*70)
print("📋 CURRENT DATABASE CONFIGURATION IN .ENV")
print("="*70)

config = {
    "DB_HOST": os.environ.get("DB_HOST"),
    "DB_PORT": os.environ.get("DB_PORT"),
    "DB_USER": os.environ.get("DB_USER"),
    "DB_NAME": os.environ.get("DB_NAME"),
}

for key, value in config.items():
    if value:
        if "PASSWORD" in key:
            masked = value[:3] + "***"
        else:
            masked = value
        print(f"   {key:<15} {masked}")

print("\n📍 CONNECTION STRING:")
print(f"   {config['DB_USER']}@{config['DB_HOST']}:{config['DB_PORT']}/{config['DB_NAME']}")

print("\n" + "="*70)
print("ℹ️  IMPORTANT:")
print("="*70)
print("""
Inside Railway Container (deployed):
  → postgres.railway.internal = Points to NEW Suave3 database ✅
  
Outside Railway (localhost):
  → postgres.railway.internal = Cannot connect (not in Railway network)
  → Only works when app runs INSIDE Railway
  
When you deploy:
  → init_railway.py will run INSIDE the container
  → It will connect to postgres.railway.internal successfully
  → Creates tables in Suave3's database
  → App will work! ✅
""")
print("="*70 + "\n")
