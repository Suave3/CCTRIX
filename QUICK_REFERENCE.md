# CCTRIX - Quick Reference Card

## 🚀 START THE APP
```bash
python app.py
```
Then visit: `http://localhost:5000`

## 🔑 DEFAULT CREDENTIALS
```
Username: admin     Password: admin123
Username: viewer    Password: viewer123
```

## 📊 KEY ENDPOINTS

### Public
```
GET  /login           - Login page
POST /login           - Submit login
GET  /logout          - Logout
GET  /health          - Health check
```

### Authenticated
```
GET  /                - Dashboard (main page)
GET  /stream          - Video stream
GET  /logs            - Detection logs JSON
GET  /stats           - Today's statistics
```

### Admin Only
```
GET  /failed-logins-page  - Failed login attempts page
GET  /login_logs          - Auth logs JSON
GET  /system-status       - System status page
GET  /export/motion       - Export detection logs CSV
GET  /export/auth         - Export auth logs CSV
```

## 📁 IMPORTANT FILES

```
app.py                    - Flask application
database.py              - Database module (all DB functions)
.env                     - Configuration (SQLite setup)
templates/               - HTML templates
static/logs/            - Detection images
cctrix.db               - SQLite database (auto-created)
```

## 🗄️ DATABASE OPERATIONS

### Initialize Database
```python
from database import init_db
init_db()  # Creates all tables
```

### Log Events
```python
from database import log_auth, log_detection, log_failed_login

# Auth event
log_auth("username", "LOGIN_SUCCESS", "reason", "192.168.1.1", "user_agent")

# Detection
log_detection(True, 0.95, "/static/logs/image.jpg")

# Failed login
log_failed_login("username", "192.168.1.1", "user_agent")
```

### Get Data
```python
from database import (
    get_recent_detections,
    get_recent_auth_logs,
    count_detections_today
)

detections = get_recent_detections(20)  # Last 20
logs = get_recent_auth_logs(50)         # Last 50
today_count = count_detections_today()  # Count today
```

## 🔄 SWITCH DATABASE TYPE

### To SQLite (recommended for development)
```bash
python setup_db.py
# Choose option 1
```

### To PostgreSQL (recommended for production)
```bash
python setup_db.py
# Choose option 2
# Enter PostgreSQL credentials
```

### To Cloud PostgreSQL (Railway/Neon/Supabase)
```bash
python setup_db.py
# Choose option 3
# Enter remote database details
```

## 📈 STATISTICS & MONITORING

### API Call Examples
```bash
# Get stats
curl http://localhost:5000/stats

# Get logs
curl http://localhost:5000/logs

# Check health
curl http://localhost:5000/health
```

### Dashboard Statistics
- Motion/Detections Today
- Failed Logins Today
- Auth Events Today

## ✅ VERIFY SETUP

```bash
# Full system check
python quick_start_check.py

# Just test database
python test_db_setup.py
```

## 🛡️ SECURITY

✅ Passwords hashed with werkzeug  
✅ reCAPTCHA v2 bot protection  
✅ Failed login tracking  
✅ IP blocking (3 failed attempts = 1 min block)  
✅ Parameterized queries (no SQL injection)  
✅ Comprehensive audit logging  

## 🚨 TROUBLESHOOTING

| Error | Fix |
|-------|-----|
| Port 5000 in use | Change port in app.py |
| Can't import database | Run `pip install -r requirements.txt` |
| No detections logged | Check camera access (CAMERA_SOURCE in .env) |
| Slow queries | Database has indexes - should be fast |
| Need to reset users | Delete cctrix.db or run `python setup_db.py` |

## 📊 DATABASE SCHEMA

```
users
├── id (PRIMARY KEY)
├── username (UNIQUE)
├── password_hash
├── role (admin/viewer)
└── created_at

detection_logs
├── id (PRIMARY KEY)
├── person_detected (BOOLEAN)
├── confidence (FLOAT)
├── image_path (TEXT)
└── detected_at (TIMESTAMP)
   └── INDEX: idx_detection_logs_detected_at

auth_logs
├── id (PRIMARY KEY)
├── username (TEXT)
├── action (LOGIN_SUCCESS/FAILED/LOGOUT)
├── reason (TEXT)
├── ip_address (TEXT)
├── user_agent (TEXT)
└── timestamp (TIMESTAMP)
   ├── INDEX: idx_auth_logs_username
   └── INDEX: idx_auth_logs_timestamp

failed_login_attempts
├── id (PRIMARY KEY)
├── username (TEXT)
├── ip_address (TEXT)
├── user_agent (TEXT)
└── attempted_at (TIMESTAMP)
   └── INDEX: idx_failed_login_ip
```

## 🔧 COMMON CONFIGURATIONS

### Local SQLite (Current)
```env
DB_TYPE=sqlite
DB_PATH=./cctrix.db
```

### Local PostgreSQL
```env
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=cctrix_db
```

### Railway Production
```env
DB_TYPE=postgresql
DB_HOST=your-railway-host.railway.internal
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_railway_password
DB_NAME=railway
```

## 🎯 TESTING THE DATABASE

```bash
# Test auth logging
curl -X POST http://localhost:5000/login \
  -d "username=admin&password=admin123"

# View recent logs
curl http://localhost:5000/logs

# Export CSV
curl http://localhost:5000/export/motion > detections.csv
```

## 📚 DOCUMENTATION

- **SETUP_COMPLETE.md** - Full setup documentation
- **DATABASE_SETUP_COMPLETE.md** - Database details
- **POSTGRES_SETUP_GUIDE.md** - PostgreSQL setup guide
- **DATABASE_README.md** - Schema documentation

## ⚡ PERFORMANCE TIPS

- Database includes performance indexes
- Connection pooling for PostgreSQL (5 connections)
- Automatic query optimization
- Timestamp filtering for fast date queries
- IP tracking for quick security checks

## 🔐 BEFORE GOING TO PRODUCTION

1. Change default passwords (admin:admin123 → strong password)
2. Change SECRET_KEY to a long random string
3. Configure real reCAPTCHA keys
4. Switch to PostgreSQL database
5. Enable HTTPS/SSL
6. Set up regular backups
7. Review security logs regularly

---

**Status:** ✅ Ready to Use  
**Database:** SQLite (Easy Swap to PostgreSQL)  
**Current Users:** 2 (admin, viewer)  
**Logging:** Fully Active

Run `python app.py` to start!
