import os
import pymysql
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Centralized configurations
MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST"),
    "port": int(os.getenv("MYSQL_PORT", 3306)),
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD")
}

POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST"),
    "port": int(os.getenv("POSTGRES_PORT", 5432)),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD")
}

# ---------- MYSQL CONNECTION ----------
def get_mysql_connection(database: str = None):
    """Connect to MySQL"""
    try:
        conn = pymysql.connect(**MYSQL_CONFIG, database=database, connect_timeout=5)
        print(f"✅ Connected to MySQL database '{database}'")
        return conn
    except Exception as e:
        print(f"❌ MySQL connection error: {e}")
        return None

def list_mysql_databases():
    """Return list of MySQL databases"""
    try:
        conn = pymysql.connect(**MYSQL_CONFIG, connect_timeout=5)
        with conn.cursor() as cursor:
            cursor.execute("SHOW DATABASES;")
            databases = [db[0] for db in cursor.fetchall()]
        conn.close()
        return databases
    except Exception as e:
        print(f"❌ Error listing MySQL databases: {e}")
        return []

# ---------- POSTGRESQL CONNECTION ----------
def get_postgres_connection(database: str = None):
    """Connect to PostgreSQL"""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG, dbname=database)
        print(f"✅ Connected to PostgreSQL database '{database}'")
        return conn
    except Exception as e:
        print(f"❌ PostgreSQL connection error: {e}")
        return None

def list_postgres_databases():
    """Return list of PostgreSQL databases"""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG, dbname="postgres")
        with conn.cursor() as cursor:
            cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
            databases = [db[0] for db in cursor.fetchall()]
        conn.close()
        return databases
    except Exception as e:
        print(f"❌ Error listing PostgreSQL databases: {e}")
        return []
