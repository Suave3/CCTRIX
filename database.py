import os
import logging
from dotenv import load_dotenv
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Auto-detect DATABASE_URL from Railway (takes precedence)
if os.environ.get("DATABASE_URL"):
    DB_TYPE = "postgresql"
    logger.info("✅ Detected DATABASE_URL - using PostgreSQL")
else:
    DB_TYPE = os.environ.get("DB_TYPE", "sqlite").lower()

if DB_TYPE == "sqlite":
    import sqlite3
    DB_PATH = os.environ.get("DB_PATH", "./cctrix.db")
    connection_pool = None
    conn = None
    
    def get_connection():
        """Get a SQLite connection"""
        global conn
        try:
            if conn is None:
                conn = sqlite3.connect(DB_PATH, check_same_thread=False)
                conn.row_factory = sqlite3.Row
                # Enable foreign keys
                conn.execute("PRAGMA foreign_keys = ON")
            return conn, conn.cursor()
        except Exception as e:
            logger.error(f"SQLite connection error: {e}")
            return None, None
    
    def close_connection():
        """Close SQLite connection"""
        pass  # Connection stays open for SQLite
    
    def execute_query(query, params=None, fetch=False):
        """Execute a query with automatic connection handling"""
        try:
            # Convert PostgreSQL %s placeholders to SQLite ? placeholders
            if DB_TYPE == "sqlite" and "%s" in query:
                query = query.replace("%s", "?")
            
            c, cur = get_connection()
            if not c or not cur:
                logger.error("Failed to get database connection")
                return None
            
            if params:
                cur.execute(query, params)
            else:
                cur.execute(query)
            
            if fetch:
                result = cur.fetchall()
                c.commit()
                return result
            else:
                c.commit()
                return True
        
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            return None

else:  # PostgreSQL
    import psycopg2
    from psycopg2 import pool, Error
    
    # Parse DATABASE_URL if it exists (for Railway)
    if os.environ.get("DATABASE_URL"):
        url = urlparse(os.environ.get("DATABASE_URL"))
        DB_CONFIG = {
            "host": url.hostname,
            "port": url.port or 5432,
            "user": url.username,
            "password": url.password,
            "database": url.path.lstrip("/"),
            "connect_timeout": 10,
            "sslmode": "require",  # Railway requires SSL
        }
        logger.info(f"✅ Using Railway PostgreSQL: {url.hostname}")
    else:
        # Get database configuration from environment variables
        DB_CONFIG = {
            "host": os.environ.get("DB_HOST", "localhost"),
            "port": int(os.environ.get("DB_PORT", "5432")),
            "user": os.environ.get("DB_USER", "postgres"),
            "password": os.environ.get("DB_PASSWORD", ""),
            "database": os.environ.get("DB_NAME", "cctrix_db"),
            "connect_timeout": int(os.environ.get("DB_CONNECT_TIMEOUT", "5")),
        }
    
    # Global connection pool (DO NOT use a global conn variable!)
    connection_pool = None
    
    def get_connection():
        """Get a database connection from the pool"""
        global connection_pool
        
        try:
            if connection_pool is None:
                connection_pool = psycopg2.pool.SimpleConnectionPool(
                    3,    # Min connections
                    30,   # Max connections (increased from 20)
                    **DB_CONFIG
                )
                logger.info("✅ Database connection pool created (3-30 connections)")
            
            # Get connection with timeout to avoid blocking
            conn = connection_pool.getconn()
            conn.autocommit = False
            return conn
        
        except Error as e:
            logger.error(f"Database connection error: {e}")
            return None
    
    def close_connection(conn):
        """Return connection to pool"""
        if conn and connection_pool:
            try:
                connection_pool.putconn(conn)
            except Exception as e:
                logger.error(f"Error returning connection to pool: {e}")
                try:
                    conn.close()
                except:
                    pass
    
    def execute_query(query, params=None, fetch=False):
        """Execute a query with proper connection management"""
        conn = None
        try:
            conn = get_connection()
            if not conn:
                logger.error("Failed to get database connection")
                return None
            
            cur = conn.cursor()
            
            if params:
                cur.execute(query, params)
            else:
                cur.execute(query)
            
            if fetch:
                result = cur.fetchall()
                conn.commit()
                cur.close()
                return result
            else:
                conn.commit()
                cur.close()
                return True
        
        except Error as e:
            logger.error(f"Query execution error: {e}")
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            return None
        finally:
            if conn:
                close_connection(conn)

def init_db():
    """Initialize database tables"""
    conn = None
    cur = None
    try:
        result = get_connection()
        
        # Handle both SQLite (returns tuple) and PostgreSQL (returns connection)
        if isinstance(result, tuple):
            conn, cur = result
        else:
            conn = result
            if conn:
                cur = conn.cursor()
        
        if not conn or not cur:
            logger.error("Cannot initialize database - no connection")
            return False
        
        if DB_TYPE == "sqlite":
            # SQLite syntax
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'viewer',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS detection_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    person_detected BOOLEAN NOT NULL,
                    confidence REAL NOT NULL,
                    image_path TEXT,
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS auth_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    action TEXT NOT NULL,
                    reason TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS failed_login_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for SQLite
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_detection_logs_detected_at 
                ON detection_logs(detected_at DESC)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_auth_logs_username 
                ON auth_logs(username)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_auth_logs_timestamp 
                ON auth_logs(timestamp DESC)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_failed_login_ip 
                ON failed_login_attempts(ip_address)
            """)
            
            conn.commit()
            logger.info("✅ SQLite database tables and indexes created successfully!")
            
        else:
            # PostgreSQL syntax
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'viewer',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS detection_logs (
                    id SERIAL PRIMARY KEY,
                    person_detected BOOLEAN NOT NULL,
                    confidence FLOAT NOT NULL,
                    image_path TEXT,
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS auth_logs (
                    id SERIAL PRIMARY KEY,
                    username TEXT NOT NULL,
                    action TEXT NOT NULL,
                    reason TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS failed_login_attempts (
                    id SERIAL PRIMARY KEY,
                    username TEXT NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for PostgreSQL
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_detection_logs_detected_at 
                ON detection_logs(detected_at DESC)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_auth_logs_username 
                ON auth_logs(username)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_auth_logs_timestamp 
                ON auth_logs(timestamp DESC)
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_failed_login_ip 
                ON failed_login_attempts(ip_address)
            """)
            
            conn.commit()
            logger.info("✅ PostgreSQL database tables and indexes created successfully!")
        
        cur.close()
        close_connection(conn)
        
        # Seed default users
        seed_users()
        return True
    
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        if conn:
            try:
                conn.rollback()
            except:
                pass
            close_connection(conn)
        return False

def log_auth(username, action, reason, ip_address, user_agent):
    """Log authentication events"""
    query = """
        INSERT INTO auth_logs (username, action, reason, ip_address, user_agent)
        VALUES (%s, %s, %s, %s, %s)
    """
    params = (username, action, reason, ip_address, user_agent)
    result = execute_query(query, params)
    if result:
        logger.info(f"✅ Auth log: {username} - {action}")
    return result

def log_failed_login(username, ip_address, user_agent):
    """Log failed login attempts"""
    query = """
        INSERT INTO failed_login_attempts (username, ip_address, user_agent)
        VALUES (%s, %s, %s)
    """
    params = (username, ip_address, user_agent)
    result = execute_query(query, params)
    if result:
        logger.info(f"✅ Failed login logged: {username} from {ip_address}")
    return result

def log_detection(person_detected, confidence, image_path):
    """Log person detection events"""
    query = """
        INSERT INTO detection_logs (person_detected, confidence, image_path)
        VALUES (%s, %s, %s)
    """
    params = (person_detected, confidence, image_path)
    result = execute_query(query, params)
    if result:
        logger.info(f"✅ Detection logged: person={person_detected}, confidence={confidence:.2f}")
    return result

def get_auth_logs(limit=100):
    """Retrieve authentication logs"""
    query = "SELECT * FROM auth_logs ORDER BY timestamp DESC LIMIT %s"
    return execute_query(query, (limit,), fetch=True)

def get_detection_logs(limit=100):
    """Retrieve detection logs"""
    query = "SELECT * FROM detection_logs ORDER BY detected_at DESC LIMIT %s"
    return execute_query(query, (limit,), fetch=True)

def get_failed_login_attempts(ip_address, minutes=60):
    """Get recent failed login attempts from an IP"""
    from datetime import datetime, timedelta
    
    time_limit = datetime.now() - timedelta(minutes=minutes)
    time_str = time_limit.isoformat()
    
    if DB_TYPE == "sqlite":
        # SQLite: convert to string format that SQLite understands (YYYY-MM-DD HH:MM:SS)
        time_str_sqlite = time_limit.strftime("%Y-%m-%d %H:%M:%S")
        query = """
            SELECT COUNT(*) FROM failed_login_attempts
            WHERE ip_address = ? 
            AND attempted_at > ?
        """
        result = execute_query(query, (ip_address, time_str_sqlite), fetch=True)
        count = result[0][0] if result else 0
        logger.info(f"SQLite query: IP {ip_address}, time_limit={time_str_sqlite}, count={count}")
        return count
    else:
        # PostgreSQL: use ISO format
        query = """
            SELECT COUNT(*) FROM failed_login_attempts
            WHERE ip_address = %s 
            AND attempted_at > %s
        """
        result = execute_query(query, (ip_address, time_str), fetch=True)
        count = result[0][0] if result else 0
        logger.info(f"PostgreSQL query: IP {ip_address}, time_limit={time_str}, count={count}")
        return count

def log(query, values):
    """Generic logging function for backward compatibility"""
    return execute_query(query, values)

def seed_users():
    """Seed default users if none exist"""
    from werkzeug.security import generate_password_hash
    
    try:
        result = execute_query("SELECT COUNT(*) FROM users", fetch=True)
        count = result[0][0] if result else 0
        
        if count == 0:
            query = """
                INSERT INTO users (username, password_hash, role) VALUES
                (%s, %s, %s), (%s, %s, %s)
            """
            params = (
                'admin', generate_password_hash('admin123'), 'admin',
                'viewer', generate_password_hash('viewer123'), 'viewer'
            )
            result = execute_query(query, params)
            if result:
                logger.info("✅ Default users seeded — admin:admin123, viewer:viewer123")
            return True
        else:
            logger.info(f"✅ Database already has {count} users")
            return True
    except Exception as e:
        logger.error(f"Error seeding users: {e}")
        return False

def get_recent_detections(limit=20):
    """Get recent detection logs"""
    query = """
        SELECT person_detected, confidence, image_path, detected_at
        FROM detection_logs
        ORDER BY id DESC
        LIMIT %s
    """
    return execute_query(query, (limit,), fetch=True)

def count_detections_today():
    """Count detection logs from today"""
    from datetime import date
    today = date.today().isoformat()
    
    if DB_TYPE == "sqlite":
        query = "SELECT COUNT(*) FROM detection_logs WHERE DATE(detected_at) = ?"
        result = execute_query(query, (today,), fetch=True)
    else:
        query = "SELECT COUNT(*) FROM detection_logs WHERE detected_at::date = %s"
        result = execute_query(query, (today,), fetch=True)
    
    return result[0][0] if result else 0

def get_recent_failed_logins(limit=50):
    """Get recent failed login attempts"""
    query = """
        SELECT username, attempted_at, ip_address, user_agent
        FROM failed_login_attempts
        ORDER BY id DESC
        LIMIT %s
    """
    return execute_query(query, (limit,), fetch=True)

def count_failed_logins_today():
    """Count failed login attempts from today"""
    from datetime import date
    today = date.today().isoformat()
    
    if DB_TYPE == "sqlite":
        query = "SELECT COUNT(*) FROM failed_login_attempts WHERE DATE(attempted_at) = ?"
        result = execute_query(query, (today,), fetch=True)
    else:
        query = "SELECT COUNT(*) FROM failed_login_attempts WHERE attempted_at::date = %s"
        result = execute_query(query, (today,), fetch=True)
    
    return result[0][0] if result else 0

def get_recent_auth_logs(limit=50):
    """Get recent authentication logs"""
    query = """
        SELECT username, action, reason, ip_address, timestamp
        FROM auth_logs
        ORDER BY id DESC
        LIMIT %s
    """
    return execute_query(query, (limit,), fetch=True)

def count_auth_logs_today():
    """Count authentication logs from today"""
    from datetime import date
    today = date.today().isoformat()
    
    if DB_TYPE == "sqlite":
        query = "SELECT COUNT(*) FROM auth_logs WHERE DATE(timestamp) = ?"
        result = execute_query(query, (today,), fetch=True)
    else:
        query = "SELECT COUNT(*) FROM auth_logs WHERE timestamp::date = %s"
        result = execute_query(query, (today,), fetch=True)
    
    return result[0][0] if result else 0

def get_all_detections():
    """Get all detection logs"""
    query = "SELECT id, person_detected, confidence, image_path, detected_at FROM detection_logs ORDER BY id DESC"
    return execute_query(query, fetch=True)

def get_all_auth_logs():
    """Get all authentication logs"""
    query = "SELECT id, username, action, reason, ip_address, user_agent, timestamp FROM auth_logs ORDER BY id DESC"
    return execute_query(query, fetch=True)

def count_total_detections():
    """Count total detection logs"""
    query = "SELECT COUNT(*) FROM detection_logs"
    result = execute_query(query, fetch=True)
    return result[0][0] if result else 0

def count_total_auth_logs():
    """Count total authentication logs"""
    query = "SELECT COUNT(*) FROM auth_logs"
    result = execute_query(query, fetch=True)
    return result[0][0] if result else 0

def count_total_users():
    """Count total users"""
    query = "SELECT COUNT(*) FROM users"
    result = execute_query(query, fetch=True)
    return result[0][0] if result else 0

def count_total_failed_logins():
    """Count total failed login attempts"""
    query = "SELECT COUNT(*) FROM failed_login_attempts"
    result = execute_query(query, fetch=True)
    return result[0][0] if result else 0