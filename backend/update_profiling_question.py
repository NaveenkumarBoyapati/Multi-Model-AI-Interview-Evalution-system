from database import get_connection

def update_question():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, role_name, question_text, expected_topics FROM Questions WHERE question_text LIKE '%data profiling%'")
    rows = cursor.fetchall()
    print("Found rows before update:")
    for r in rows:
        print(" ", r)

    new_topics = "examining dataset structure, data types, missing values, duplicates, distributions, quality issues"
    cursor.execute("""
        UPDATE Questions
        SET expected_topics = ?
        WHERE question_text LIKE '%data profiling%'
    """, (new_topics,))
    conn.commit()

    cursor.execute("SELECT id, role_name, question_text, expected_topics FROM Questions WHERE question_text LIKE '%data profiling%'")
    updated_rows = cursor.fetchall()
    print("\nFound rows after update:")
    for r in updated_rows:
        print(" ", r)

    cursor.close()
    conn.close()

if __name__ == "__main__":
    update_question()
