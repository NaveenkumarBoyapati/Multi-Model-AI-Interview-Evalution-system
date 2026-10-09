from database import get_connection

def update_web_question():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, role_name, question_text, expected_topics FROM Questions WHERE id=1844 OR question_text LIKE '%responsive web design%'")
    rows = cursor.fetchall()
    print("Found rows before update:")
    for r in rows:
        print(" ", r)

    new_topics = "responsive web design, media queries, viewport, breakpoints, fluid layout and flexible images, mobile-first design"
    cursor.execute("""
        UPDATE Questions
        SET expected_topics = ?
        WHERE id = 1844 OR LOWER(LTRIM(RTRIM(question_text))) = LOWER('What is responsive web design and media queries?')
    """, (new_topics,))
    conn.commit()

    cursor.execute("SELECT id, role_name, question_text, expected_topics FROM Questions WHERE id=1844 OR question_text LIKE '%responsive web design%'")
    updated_rows = cursor.fetchall()
    print("\nFound rows after update:")
    for r in updated_rows:
        print(" ", r)

    cursor.close()
    conn.close()

if __name__ == "__main__":
    update_web_question()
