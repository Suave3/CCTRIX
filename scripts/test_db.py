import os, traceback
from dotenv import load_dotenv
load_dotenv()
import psycopg2

cfg = {
    'host': os.environ.get('DB_HOST'),
    'port': os.environ.get('DB_PORT'),
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASSWORD'),
    'database': os.environ.get('DB_NAME')
}
print('Testing DB config:', cfg)
try:
    conn = psycopg2.connect(**cfg)
    print('DB CONNECTED')
    conn.close()
except Exception:
    traceback.print_exc()
