# 📊 CCTRIX Database Logs - Complete Overview

Generated: June 4, 2026

---

## 📋 Database Summary

Your CCTRIX database currently contains:

| Category | Count | Details |
|----------|-------|---------|
| **Users** | 2 | admin (admin role), viewer (viewer role) |
| **Failed Logins** | 2 | 2 attempts from IP 192.168.1.4 |
| **Auth Events** | 7 | Including logins, logouts, and failed attempts |
| **Detection Logs** | 25 | All with person detected (90% confidence) |

---

## 👥 Registered Users

```
1. admin
   └─ Role: admin (full access)
   └─ Created: 2026-06-04 09:16:47

2. viewer
   └─ Role: viewer (read-only)
   └─ Created: 2026-06-04 09:16:47
```

---

## ⚠️ Failed Login Attempts

```
Total Failed Attempts: 2

Attempt 1:
├─ Username: LeaOtnisDin
├─ IP Address: 192.168.1.4
├─ Time: 2026-06-04 09:21:43
└─ User Agent: Chrome/148.0.0.0 (Windows)

Attempt 2:
├─ Username: PatrickOtnisToTheMax
├─ IP Address: 192.168.1.4
├─ Time: 2026-06-04 09:19:33
└─ User Agent: Chrome/148.0.0.0 (Windows)

⚠️ NOTE: These are blocked attempts - good security feature!
```

---

## 🔐 Authentication Log

```
Total Events: 7

Chronological Order:

1. [09:17:26] test @ 127.0.0.1
   Action: TEST
   Reason: Test action

2. [09:19:33] PatrickOtnisToTheMax @ 192.168.1.4
   Action: LOGIN_FAILED
   Reason: Invalid credentials

3. [09:19:54] admin @ 192.168.1.4
   Action: LOGIN_SUCCESS
   Reason: Valid credentials

4. [09:21:26] admin @ 192.168.1.4
   Action: LOGOUT
   Reason: User logged out

5. [09:21:43] LeaOtnisDin @ 192.168.1.4
   Action: LOGIN_FAILED
   Reason: Invalid credentials

6. [09:22:01] viewer @ 192.168.1.4
   Action: LOGIN_SUCCESS
   Reason: Valid credentials

7. [09:22:39] viewer @ 192.168.1.4
   Action: LOGOUT
   Reason: User logged out
```

---

## 🎥 Detection Logs

```
Total Detections: 25 (showing last 10)

All detections have:
├─ Person Detected: ✅ YES
├─ Confidence: 90.0%
└─ Images saved to: /static/logs/

Latest Detections:
├─ ID 25: 2026-06-04 09:22:37 - /static/logs/1780564957.jpg
├─ ID 24: 2026-06-04 09:22:31 - /static/logs/1780564951.jpg
├─ ID 23: 2026-06-04 09:22:26 - /static/logs/1780564946.jpg
├─ ID 22: 2026-06-04 09:22:21 - /static/logs/1780564941.jpg
├─ ID 21: 2026-06-04 09:22:16 - /static/logs/1780564936.jpg
├─ ID 20: 2026-06-04 09:22:11 - /static/logs/1780564931.jpg
├─ ID 19: 2026-06-04 09:22:06 - /static/logs/1780564926.jpg
├─ ID 18: 2026-06-04 09:22:01 - /static/logs/1780564881.jpg
├─ ID 17: 2026-06-04 09:21:21 - /static/logs/1780564821.jpg
└─ ID 16: 2026-06-04 09:21:16 - /static/logs/1780564876.jpg

... and 15 more detections
```

---

## 📅 Daily Statistics

```
Today's Activity (2026-06-04):

├─ Detections: 25
├─ Auth Events: 7
├─ Failed Logins: 2
└─ New Users: 0
```

---

## 🔄 PostgreSQL Connection String

You found: `${{ Postgres.DATABASE_URL }}`

This is a **Railway template variable** that needs to be replaced with actual connection details.

### How to Use It:

**If you have a Railway PostgreSQL database:**

1. Copy the actual connection string from your Railway dashboard
2. Run the configuration script:
   ```bash
   python configure_postgres.py
   ```
3. Paste your connection string when prompted
4. The script will automatically update your `.env` file

### Connection String Format:

```
postgresql://username:password@host:port/database
```

Example from Railway:
```
postgresql://postgres:abc123xyz@postgres.railway.internal:5432/railway
```

### Manual Configuration:

If you prefer to enter details manually:

```bash
python configure_postgres.py
# Choose manual entry option
# Enter your connection details
```

---

## 🚀 Using Your PostgreSQL Database

### Step 1: Get Your Connection Details

From Railway dashboard, look for:
- **Host**: postgres.railway.internal or similar
- **Port**: 5432 (usually)
- **Username**: postgres
- **Password**: Your Railway password
- **Database**: railway or your database name

### Step 2: Configure CCTRIX

Option A - Use the configuration script:
```bash
python configure_postgres.py
```

Option B - Manual configuration:
1. Edit `.env` file
2. Change these lines:
```env
DB_TYPE=postgresql
DB_HOST=your_host
DB_PORT=5432
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=your_database
```

### Step 3: Test Connection

```bash
python test_db_setup.py
```

You should see:
```
✅ All environment variables set
✅ Database module imported
✅ Database initialized successfully!
✅ Auth logging works
✅ Detection logging works
✅ ALL TESTS PASSED!
```

### Step 4: Start Your Application

```bash
python app.py
```

---

## 📊 Viewing Logs

### Method 1: Command Line
```bash
# View all logs formatted nicely
python view_logs.py

# Or detailed retrieval
python retrieve_logs.py
```

### Method 2: Web Interface
```
http://localhost:5000

Login as:
├─ Username: admin
├─ Password: admin123
└─ Navigate to "Logs" page
```

### Method 3: Export as CSV
```
GET /export/motion    - Download detection logs as CSV
GET /export/auth      - Download auth logs as CSV
```

### Method 4: API Endpoints
```bash
# Get recent logs as JSON
curl http://localhost:5000/logs

# Get statistics
curl http://localhost:5000/stats

# Get auth logs (admin only)
curl http://localhost:5000/login_logs
```

---

## 🔧 Available Tools

### Log Retrieval
```bash
python view_logs.py                    # Simple, formatted view
python retrieve_logs.py                # Detailed retrieval
```

### Database Configuration
```bash
python setup_db.py                     # Interactive setup wizard
python configure_postgres.py           # PostgreSQL URL parser
python test_db_setup.py               # Connection tester
```

### Application
```bash
python app.py                          # Start the Flask app
python quick_start_check.py           # System verification
```

---

## 📝 Database Functions

If you want to work with logs programmatically:

```python
from database import (
    # Users
    count_total_users,
    
    # Detections
    get_recent_detections,
    count_detections_today,
    count_total_detections,
    
    # Authentication
    get_recent_auth_logs,
    count_auth_logs_today,
    count_total_auth_logs,
    
    # Failed Logins
    get_recent_failed_logins,
    count_failed_logins_today,
    count_total_failed_logins,
    
    # Logging
    log_auth,
    log_detection,
    log_failed_login,
)

# Example: Get recent detections
detections = get_recent_detections(limit=20)
for detection in detections:
    print(detection)

# Example: Get today's stats
today_count = count_detections_today()
print(f"Detections today: {today_count}")
```

---

## 🔐 Security Features

Your database is currently tracking:

✅ **Failed Login Attempts**
- Tracks username, IP, and user agent
- IP blocking after 3 failed attempts
- 1-minute lockout period

✅ **Authentication Audit Trail**
- Records every login/logout
- Captures IP address and browser info
- Logs success/failure with reason

✅ **Detection Logging**
- Records every person detection
- Includes confidence scores
- Saves image evidence

✅ **User Accounts**
- Password hashed with werkzeug
- Role-based access control
- Created timestamps

---

## 📈 Next Steps

### Immediate
1. ✅ View your logs: `python view_logs.py`
2. ✅ Check database connection: `python test_db_setup.py`
3. ✅ Start the app: `python app.py`

### Short Term
1. Configure PostgreSQL with your connection string
2. Test the PostgreSQL connection
3. Verify logs work with PostgreSQL
4. Change default passwords (optional)

### Long Term
1. Set up regular backups
2. Monitor logs for security
3. Archive old detection images
4. Deploy to production

---

## 🆘 Troubleshooting

### Q: How do I get my Postgres.DATABASE_URL?
**A:** 
- If using Railway: Check Project Settings → Database → URI
- If using other service: Check connection strings in your dashboard
- Format should be: `postgresql://user:password@host:port/database`

### Q: Connection string has special characters?
**A:** URL encode them:
- `@` → `%40`
- `#` → `%23`
- `%` → `%25`
- `:` → `%3A` (only in password)

Or use the configuration script - it handles encoding automatically.

### Q: My PostgreSQL password has special characters?
**A:** The configure_postgres.py script handles URL encoding automatically.

### Q: How do I switch back to SQLite?
**A:** 
```bash
python setup_db.py
# Choose option 1 for SQLite
```

### Q: Do I lose my data when switching databases?
**A:** Yes. Migrate your data first if needed using the export functions.

---

## 💾 Backup Your Data

### SQLite Backup
```bash
cp cctrix.db cctrix.db.backup
```

### PostgreSQL Backup
```bash
pg_dump -U postgres -d your_database > backup.sql
```

### Export Logs
```bash
# Via web interface
curl http://localhost:5000/export/motion > detections.csv
curl http://localhost:5000/export/auth > auth.csv

# Via Python
python view_logs.py > logs_backup.txt
```

---

## 📞 Summary

**Current Database:**
- Type: SQLite (local development)
- Location: ./cctrix.db
- Records: 25 detections, 7 auth events, 2 failed logins

**Ready to Migrate to PostgreSQL:**
- Have your connection string ready
- Run: `python configure_postgres.py`
- Paste your PostgreSQL.DATABASE_URL
- Done! ✅

**Getting Your Logs:**
- View: `python view_logs.py`
- Export: `curl http://localhost:5000/export/motion`
- API: `curl http://localhost:5000/logs`

---

Generated: June 4, 2026  
Database: SQLite ➜ Ready for PostgreSQL  
Status: ✅ Fully Functional
