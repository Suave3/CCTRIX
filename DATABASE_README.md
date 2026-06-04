# 📊 CCTRIX Database Management Guide

## Database Status: ✅ FULLY OPERATIONAL

Your CCTV system uses **PostgreSQL** for storing user accounts, detection logs, authentication events, and security tracking.

---

## 📋 Database Schema

### Tables

#### 1. **users** - User Accounts
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'viewer',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```
**Roles:**
- `admin` - Full access to all features
- `viewer` - View-only access to camera feeds and logs

#### 2. **detection_logs** - Person Detection Records
```sql
CREATE TABLE detection_logs (
    id SERIAL PRIMARY KEY,
    person_detected BOOLEAN,
    confidence FLOAT,
    image_path TEXT,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```
**Purpose:** Tracks every person detection event with confidence score and image evidence.

#### 3. **auth_logs** - Authentication History
```sql
CREATE TABLE auth_logs (
    id SERIAL PRIMARY KEY,
    username TEXT,
    action TEXT,
    reason TEXT,
    ip_address TEXT,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```
**Actions Tracked:**
- `LOGIN` - User login
- `LOGIN_SUCCESS` - Successful authentication
- `LOGIN_FAILED` - Failed login attempt
- `LOGOUT` - User logout

#### 4. **failed_login_attempts** - Security Tracking
```sql
CREATE TABLE failed_login_attempts (
    id SERIAL PRIMARY KEY,
    username TEXT,
    ip_address TEXT,
    user_agent TEXT,
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```
**Purpose:** Prevents brute-force attacks by tracking failed login attempts.

---

## 🔧 Database Management Commands

### 1. **Health Check** (Recommended - Run First)
```bash
python db_health_check.py
```
Shows complete database status, table sizes, data integrity, and all indexes.

### 2. **Repair Database** (If Corrupted)
```bash
python db_health_check.py repair
```
⚠️ **WARNING:** This will DROP and RECREATE all tables! Only use if absolutely necessary. Backs up data first!

### 3. **View Statistics**
```bash
python db_manage.py stats
```
Shows row counts, detection statistics, and recent auth activity.

### 4. **Create Admin User**
```bash
python db_manage.py admin <username> <password>
```
**Example:**
```bash
python db_manage.py admin john secure_password_123
```

### 5. **Clean Old Logs** (Maintenance)
```bash
python db_manage.py cleanup 30
```
Removes logs older than 30 days. Adjust number as needed.

### 6. **Export Schema**
```bash
python db_manage.py export
```
Saves database schema to `database_schema.json` for documentation.

---

## 📊 Current Database Status

| Component | Status | Details |
|-----------|--------|---------|
| **Connection** | ✅ | PostgreSQL 18.4 on Railway |
| **Tables** | ✅ | 4 tables (users, detection_logs, auth_logs, failed_login_attempts) |
| **Data** | ✅ | 499 records total |
| **Indexes** | ✅ | 11 indexes for performance |
| **Constraints** | ✅ | 12 constraints enforced |
| **Size** | ✅ | 8.2 MB |

### Data Breakdown
- **Users:** 2 (admin, viewer)
- **Detection Logs:** 410 (384 confirmed detections, 90% avg confidence)
- **Auth Logs:** 62 events
- **Failed Attempts:** 25 tracked

---

## 🚀 Deployment Instructions

### Local Development
```bash
# Initialize database
python init_database.py

# Check status
python db_manage.py stats
```

### Railway Cloud Deployment
1. Database automatically created from `init_database.py`
2. Environment variables in `.env` define connection:
   - `DB_HOST=postgres.railway.internal`
   - `DB_PORT=5432`
   - `DB_USER=postgres`
   - `DB_PASSWORD=your_password`
   - `DB_NAME=railway`

---

## 🔐 Security Best Practices

### Password Hashing
All passwords are hashed using **werkzeug.security.generate_password_hash**:
```python
from werkzeug.security import generate_password_hash, check_password_hash

password_hash = generate_password_hash("password123")
is_correct = check_password_hash(password_hash, "password123")
```

### SQL Injection Prevention
All queries use **parameterized statements**:
```python
# ✅ SAFE - Uses parameterized queries
cursor.execute("SELECT * FROM users WHERE username = %s", (username,))

# ❌ UNSAFE - String interpolation
cursor.execute(f"SELECT * FROM users WHERE username = '{username}'")
```

### Failed Login Tracking
System automatically tracks failed login attempts and can block IPs:
```bash
python db_manage.py stats  # See failed attempts
```

---

## 🔍 Database Connection Details

**Local/Development:**
```python
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=cctrix_db
```

**Railway Production:**
```python
DB_HOST=postgres.railway.internal
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=railway
```

---

## 📈 Performance Indexes

All tables have optimized indexes for fast queries:

| Index | Table | Column | Purpose |
|-------|-------|--------|---------|
| `idx_detection_logs_detected_at` | detection_logs | detected_at | Fast date range queries |
| `idx_auth_logs_timestamp` | auth_logs | timestamp | Recent activity queries |
| `idx_auth_logs_username` | auth_logs | username | User activity lookup |
| `idx_failed_login_username` | failed_login_attempts | username | Brute force detection |
| `idx_failed_login_attempted_at` | failed_login_attempts | attempted_at | Recent attempts lookup |
| `idx_users_username` | users | username | Fast user lookup |

---

## 🛠️ Troubleshooting

### Database Connection Failed
```bash
# Check connection string
echo $DB_HOST $DB_PORT $DB_USER $DB_NAME

# Test connection
python -c "import psycopg2; psycopg2.connect(user='postgres', host='localhost')"
```

### Tables Missing
```bash
# Initialize/repair database
python db_health_check.py repair
```

### Performance Issues
```bash
# Check database size
python db_manage.py stats

# Clean old logs
python db_manage.py cleanup 30
```

### Connection Timeout
```bash
# Increase timeout in app.py
DB_CONNECT_TIMEOUT=10  # seconds
```

---

## 📝 Database Backup/Restore

### PostgreSQL Dump (Backup)
```bash
pg_dump -U postgres -h localhost railway > backup.sql
```

### Restore from Backup
```bash
psql -U postgres -h localhost railway < backup.sql
```

### Using Railway CLI
```bash
# Connect to Railway database
railway connect

# Backup command in Railway
pg_dump -h postgres.railway.internal -U postgres railway > backup.sql
```

---

## 🚀 Next Steps

1. ✅ **Database initialized** - All tables created and indexed
2. ✅ **Data verified** - 499 records stored successfully
3. ✅ **Security configured** - Password hashing and SQL injection prevention
4. **Deploy to Railway** - Configure environment variables and deploy
5. **Monitor database** - Use health check tool regularly

---

## 📞 Support

For database issues, run:
```bash
# Comprehensive health check
python db_health_check.py

# If repair needed
python db_health_check.py repair
```

All database management tools are in the project root directory.
