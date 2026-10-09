import os
import pyodbc
from env_loader import load_env

load_env()

# Configurable database settings with local defaults
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


def get_connection():
    return pyodbc.connect(CONNECTION_STRING)
