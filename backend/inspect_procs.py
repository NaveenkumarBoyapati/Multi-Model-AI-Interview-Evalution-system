from database import get_connection

def inspect_procs():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, type_desc FROM sys.objects WHERE type IN ('P', 'TR', 'V', 'FN')")
    rows = cursor.fetchall()
    print("Database objects (Procedures, Triggers, Views, Functions):")
    for r in rows:
        print(f"  {r[0]} ({r[1]})")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    inspect_procs()
