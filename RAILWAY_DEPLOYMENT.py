#!/usr/bin/env python3
"""
CCTRIX Railway Deployment Guide
Deploy your CCTRIX app to Railway with PostgreSQL
"""

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║         CCTRIX RAILWAY DEPLOYMENT GUIDE                                    ║
║     Deploy to Railway for Free PostgreSQL Database Access                 ║
╚════════════════════════════════════════════════════════════════════════════╝

✅ YOUR APP IS READY FOR RAILWAY DEPLOYMENT!

Here's how to deploy your CCTRIX system to Railway:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 1: CREATE requirements.txt
────────────────────────────────────────────────────────────────────────────

Run this command to create requirements.txt:

    pip freeze > requirements.txt

OR manually create requirements.txt with:

    Flask==2.3.3
    psycopg2-binary==2.9.7
    python-dotenv==1.0.0
    opencv-python==4.8.1.78
    werkzeug==2.3.7
    Pillow==10.0.0

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 2: CREATE Procfile
────────────────────────────────────────────────────────────────────────────

Create a file named "Procfile" (no extension) in your project root:

    web: python app.py

This tells Railway how to start your app.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 3: PUSH TO GITHUB
────────────────────────────────────────────────────────────────────────────

Railway deploys from GitHub. Push your code:

    git init
    git add .
    git commit -m "CCTRIX initial deployment"
    git remote add origin https://github.com/YOUR_USERNAME/cctrix.git
    git push -u origin main

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 4: DEPLOY TO RAILWAY
────────────────────────────────────────────────────────────────────────────

1. Go to https://railway.app/
2. Click "Create New Project"
3. Choose "Deploy from GitHub"
4. Select your cctrix repository
5. Wait for deployment to complete ✅

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 5: ENVIRONMENT VARIABLES
────────────────────────────────────────────────────────────────────────────

In your Railway project settings, the app will AUTOMATICALLY:

✅ Auto-detect the DATABASE_URL from your PostgreSQL service
✅ Parse the connection string
✅ Connect to PostgreSQL on Railway
✅ Create all tables automatically (first run)
✅ Start logging to PostgreSQL immediately

You can add optional variables in Railway dashboard:

    SECRET_KEY=your_long_random_secret_here
    CAMERA_SOURCE=0
    RECAPTCHA_SITE_KEY=6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI
    RECAPTCHA_SECRET_KEY=6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ17ZFtSe

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STEP 6: VERIFY DEPLOYMENT
────────────────────────────────────────────────────────────────────────────

Once deployed:

1. Click "Open Railway App" from your project
2. You'll see your CCTRIX app running
3. Login with:
   - Username: admin
   - Password: admin123

4. Check the database:
   - Go to your Postgres service in Railway
   - Click "Data" tab
   - You should see the 4 tables populated:
     └─ users
     └─ auth_logs
     └─ detection_logs
     └─ failed_login_attempts

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HOW THE DATABASE WORKS
────────────────────────────────────────────────────────────────────────────

When your app runs on Railway:

1. Railway automatically provides DATABASE_URL environment variable
2. CCTRIX database module detects it
3. Automatically parses PostgreSQL connection details
4. Connects to your Railway PostgreSQL database
5. Creates tables on first run (if they don't exist)
6. All logs automatically store in PostgreSQL:
   ✅ User logins/logouts
   ✅ Failed login attempts
   ✅ Person detections
   ✅ All with timestamps and audit info

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

VIEWING LOGS IN RAILWAY DATABASE
────────────────────────────────────────────────────────────────────────────

Via web interface:
  http://your-app.railway.app/logs

Via API:
  curl https://your-app.railway.app/logs
  curl https://your-app.railway.app/stats
  curl https://your-app.railway.app/login_logs

Via Railway dashboard:
  1. Click PostgreSQL service
  2. Click "Data" tab
  3. Click each table to view records
  4. Scroll to see all logs

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TOTAL COST
────────────────────────────────────────────────────────────────────────────

Railway free tier includes:
  ✅ $5 free credit per month
  ✅ 1 PostgreSQL database
  ✅ 100 hours of uptime
  ✅ Enough for testing and small deployments

Your CCTRIX app will cost approximately:
  • $2-3/month for the app service
  • PostgreSQL is FREE on Railway
  • Total: Very affordable

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TROUBLESHOOTING
────────────────────────────────────────────────────────────────────────────

❌ App crashes on deployment?
   → Check Railway logs: Click app → Deployments → View Logs
   → Common issue: Missing requirements.txt

❌ Tables not created?
   → This is normal on first run
   → Refresh your browser after a few seconds
   → Check Railway logs for initialization messages

❌ Can't login?
   → Default users are created automatically
   → Username: admin
   → Password: admin123

❌ Logs not appearing in database?
   → Check Railway PostgreSQL is running
   → Verify DATABASE_URL is detected (check logs)
   → Wait a few seconds for data to sync

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

NEXT STEPS
────────────────────────────────────────────────────────────────────────────

1. Create requirements.txt
2. Create Procfile
3. Push to GitHub
4. Deploy to Railway
5. Watch your logs appear in PostgreSQL!

Questions? Check Railway docs: https://docs.railway.app/

╚════════════════════════════════════════════════════════════════════════════╝
""")
