"""
Azure SQL Database Connectivity & Health Diagnostic Script.

Tests connectivity to Azure SQL Database using current .env configuration,
verifies driver, permissions, and database response.
"""

import sys
import os
import pyodbc

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from env_loader import load_env
from database import get_connection, CONNECTION_STRING

load_env()

def test_azure_db():
    print("=" * 60)
    print("AZURE SQL DATABASE DIAGNOSTIC TEST")
    print("=" * 60)

    # Mask password for display
    masked_cs = CONNECTION_STRING
    if "PWD=" in masked_cs:
        parts = masked_cs.split("PWD=")
        pwd_part = parts[1].split(";")[0]
        masked_cs = masked_cs.replace(f"PWD={pwd_part}", "PWD=********")

    print(f"Connecting with: {masked_cs}\n")

    try:
        conn = get_connection()
        cursor = conn.cursor()

        print("[OK] Connection established successfully!")

        cursor.execute("SELECT DB_NAME(), @@VERSION")
        row = cursor.fetchone()
        db_name, version = row[0], row[1]
        print(f"[OK] Database Name: {db_name}")
        print(f"[OK] Engine Version: {version[:80]}...")

        # Check if tables exist
        cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
        table_count = cursor.fetchone()[0]
        print(f"[INFO] Existing Base Tables Count: {table_count}")

        cursor.close()
        conn.close()
        print("\n[SUCCESS] Azure SQL Database is ready for deployment!")
        return True

    except pyodbc.Error as exc:
        sqlstate = exc.args[0] if exc.args else ""
        err_msg = str(exc)
        print("\n[ERROR] Connection failed!")
        print(f"Details: {err_msg}\n")

        if "Cannot open server" in err_msg or "Client with IP address" in err_msg or "40615" in err_msg:
            print(">>> FIX: Firewall Issue!")
            print("1. Go to Azure Portal -> Your SQL Server -> Security -> Networking")
            print("2. Check 'Allow Azure services and resources to access this server'")
            print("3. Click 'Add your client IPv4 address' and Save.")
        elif "Login failed" in err_msg or "18456" in err_msg:
            print(">>> FIX: Authentication Issue!")
            print("Check DB_USER and DB_PASSWORD in your .env file.")
        elif "Cannot open database" in err_msg or "4060" in err_msg:
            print(">>> FIX: Database Name Issue!")
            print("Ensure the database name specified in DB_NAME exists on the SQL Server.")
        return False

if __name__ == "__main__":
    test_azure_db()
