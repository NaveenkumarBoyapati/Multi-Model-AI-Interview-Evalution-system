from database import get_connection

def inspect_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT TOP 5 * FROM Users")
    print([c[0] for c in cursor.description])
    for r in cursor.fetchall():
        print(r)
    cursor.close()
    conn.close()

if __name__ == "__main__":
    inspect_users()
