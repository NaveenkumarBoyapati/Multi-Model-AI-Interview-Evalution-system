import os
import sqlite3
import datetime
import re
from env_loader import load_env

load_env()

# DB ENGINE: "sqlite" (default for zero-dependency cloud/Docker) or "mssql" (for local SQL Server / Azure SQL)
DB_ENGINE = os.getenv("DB_ENGINE", "").lower().strip()
SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "interview_system.db")

# -------------------------------------------------------------
# MSSQL CONFIGURATION (PYODBC)
# -------------------------------------------------------------
DRIVER = os.getenv("DB_DRIVER", "{ODBC Driver 18 for SQL Server}")
SERVER = os.getenv("DB_SERVER", "EXPLORER")
DATABASE = os.getenv("DB_NAME", os.getenv("DB_DATABASE", "AIInterviewDB"))
USER = os.getenv("DB_USER", "").strip()
PASSWORD = os.getenv("DB_PASSWORD", "").strip()
TRUST_CERT = os.getenv("DB_TRUST_SERVER_CERTIFICATE", "yes")
ENCRYPT = os.getenv("DB_ENCRYPT", "yes" if USER else "no")
TIMEOUT = os.getenv("DB_TIMEOUT", "30")

if USER and PASSWORD:
    CONNECTION_STRING = (
        f"DRIVER={DRIVER};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        f"UID={USER};"
        f"PWD={PASSWORD};"
        f"Encrypt={ENCRYPT};"
        f"TrustServerCertificate={TRUST_CERT};"
        f"Connection Timeout={TIMEOUT};"
    )
else:
    TRUSTED_CONN = os.getenv("DB_TRUSTED_CONNECTION", "yes")
    CONNECTION_STRING = (
        f"DRIVER={DRIVER};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        f"Trusted_Connection={TRUSTED_CONN};"
        f"TrustServerCertificate={TRUST_CERT};"
    )

# -------------------------------------------------------------
# SQLITE COMPATIBILITY LAYER & QUERY TRANSLATOR
# -------------------------------------------------------------

def translate_sql(sql: str) -> str:
    cleaned = sql.strip()
    
    # 1. OUTPUT INSERTED.id -> RETURNING id
    if re.search(r"OUTPUT\s+INSERTED\.\[?id\]?", cleaned, re.IGNORECASE):
        cleaned = re.sub(r"OUTPUT\s+INSERTED\.\[?id\]?", "", cleaned, flags=re.IGNORECASE)
        cleaned = cleaned.rstrip().rstrip(";") + " RETURNING id"
        
    # 2. SELECT TOP (\d+) ... -> SELECT ... LIMIT \1
    top_match = re.search(r"SELECT\s+TOP\s+(\d+|{\w+})\s+", cleaned, re.IGNORECASE)
    if top_match:
        limit_val = top_match.group(1)
        cleaned = re.sub(r"SELECT\s+TOP\s+(\d+|{\w+})\s+", "SELECT ", cleaned, count=1, flags=re.IGNORECASE)
        cleaned = cleaned.rstrip().rstrip(";") + f" LIMIT {limit_val}"
        
    # 3. Strip SQL Server table hints like WITH (NOLOCK)
    cleaned = re.sub(r"WITH\s*\(\s*NOLOCK\s*\)", "", cleaned, flags=re.IGNORECASE)
    
    # 4. Handle DATEADD(unit, val, date_expr) where unit is unquoted
    cleaned = re.sub(r"DATEADD\s*\(\s*([a-zA-Z]+)\s*,", r"DATEADD('\1',", cleaned, flags=re.IGNORECASE)
        
    return cleaned

def parse_db_value(val):
    if isinstance(val, str) and len(val) >= 19:
        if val[4] == '-' and val[7] == '-' and val[10] in (' ', 'T') and val[13] == ':' and val[16] == ':':
            try:
                return datetime.datetime.strptime(val[:19].replace('T', ' '), '%Y-%m-%d %H:%M:%S')
            except Exception:
                pass
    return val

def _format_row(row):
    if row is None:
        return None
    return tuple(parse_db_value(v) for v in row)

class SQLiteCursorWrapper:
    def __init__(self, raw_cursor):
        self._cur = raw_cursor

    def execute(self, sql, params=None):
        translated = translate_sql(sql)
        if params is not None:
            if not isinstance(params, (tuple, list, dict)):
                params = (params,)
            return self._cur.execute(translated, params)
        return self._cur.execute(translated)

    def executemany(self, sql, seq_of_params):
        translated = translate_sql(sql)
        return self._cur.executemany(translated, seq_of_params)

    def fetchone(self):
        row = self._cur.fetchone()
        return _format_row(row)

    def fetchall(self):
        rows = self._cur.fetchall()
        return [_format_row(r) for r in rows]

    def fetchmany(self, size=None):
        rows = self._cur.fetchmany(size) if size else self._cur.fetchmany()
        return [_format_row(r) for r in rows]

    @property
    def description(self):
        return self._cur.description

    @property
    def rowcount(self):
        return self._cur.rowcount

    def close(self):
        self._cur.close()

class SQLiteConnectionWrapper:
    def __init__(self, raw_conn):
        self._conn = raw_conn

    def cursor(self):
        return SQLiteCursorWrapper(self._conn.cursor())

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

def sqlite_dateadd(unit, amount, dt_str):
    try:
        dt = datetime.datetime.strptime(str(dt_str)[:19], "%Y-%m-%d %H:%M:%S")
    except Exception:
        dt = datetime.datetime.now()
    if str(unit).lower() in ("day", "days", "d"):
        res = dt + datetime.timedelta(days=int(amount))
    elif str(unit).lower() in ("minute", "minutes", "mi"):
        res = dt + datetime.timedelta(minutes=int(amount))
    elif str(unit).lower() in ("hour", "hours", "hh"):
        res = dt + datetime.timedelta(hours=int(amount))
    else:
        res = dt + datetime.timedelta(days=int(amount))
    return res.strftime("%Y-%m-%d %H:%M:%S")

def get_sqlite_connection():
    # Ensure database schema is initialized on first connect
    from sqlite_init import init_sqlite_db
    if not os.path.exists(SQLITE_DB_PATH) or os.path.getsize(SQLITE_DB_PATH) == 0:
        init_sqlite_db(SQLITE_DB_PATH)
        
    raw = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
    raw.execute("PRAGMA journal_mode=WAL")
    raw.execute("PRAGMA foreign_keys=ON")
    
    raw.create_function("GETUTCDATE", 0, lambda: datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
    raw.create_function("GETDATE", 0, lambda: datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    raw.create_function("SYSDATETIME", 0, lambda: datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    raw.create_function("SYSUTCDATETIME", 0, lambda: datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S"))
    raw.create_function("DATEADD", 3, sqlite_dateadd)
    
    return SQLiteConnectionWrapper(raw)

# -------------------------------------------------------------
# UNIFIED GET_CONNECTION FUNCTION
# -------------------------------------------------------------

def get_connection():
    if DB_ENGINE == "sqlite":
        return get_sqlite_connection()
    
    try:
        import pyodbc
        return pyodbc.connect(CONNECTION_STRING)
    except Exception as exc:
        # If pyodbc or MSSQL connection fails, fallback automatically to SQLite
        return get_sqlite_connection()