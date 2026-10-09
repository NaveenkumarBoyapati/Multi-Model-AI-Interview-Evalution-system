from database import get_connection

def inspect_questions_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role_name, COUNT(*) FROM Questions GROUP BY role_name")
    for r in cursor.fetchall():
        print(f"Role: {r[0]} | Question count: {r[1]}")

    cursor.execute("SELECT COUNT(*) FROM Users")
    print("Users count:", cursor.fetchone()[0])

    cursor.execute("SELECT COUNT(*) FROM Roles")
    print("Roles count:", cursor.fetchone()[0])

    cursor.close()
    conn.close()

if __name__ == "__main__":
    inspect_questions_table()
