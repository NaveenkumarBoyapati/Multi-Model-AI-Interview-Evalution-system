from database import get_connection

def test_q_matching():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, role_name, question_text, category, difficulty FROM Questions")
    rows = cursor.fetchall()
    print(f"Total questions in Questions table: {len(rows)}")

    # Test some sample questions from our interview questions
    sample_tests = [
        "Tell me about yourself.",
        "Why do you want to work in this field?",
        "What is Python and what are its main features?",
        "What is the difference between a list and a tuple in Python?",
        "What is a pivot table?",
        "What is SQL and what is it used for?"
    ]

    q_map = {}
    for r in rows:
        clean_text = " ".join(r[2].lower().strip().split())
        q_map[clean_text] = (r[0], r[1], r[3], r[4], r[2])

    for st in sample_tests:
        clean_st = " ".join(st.lower().strip().split())
        match = q_map.get(clean_st)
        if match:
            print(f"EXACT MATCH: '{st}' -> id={match[0]}, role={match[1]}, cat={match[2]}, diff={match[3]}")
        else:
            # Token overlap match
            st_words = set(clean_st.replace("?", "").replace(".", "").split())
            best_score = 0.0
            best_match = None
            for q_clean, q_data in q_map.items():
                q_words = set(q_clean.replace("?", "").replace(".", "").split())
                inter = len(st_words & q_words)
                union = len(st_words | q_words)
                score = inter / float(union) if union > 0 else 0.0
                if score > best_score:
                    best_score = score
                    best_match = q_data
            if best_score >= 0.5:
                print(f"FUZZY MATCH ({best_score:.2f}): '{st}' -> id={best_match[0]}, text='{best_match[4]}'")
            else:
                print(f"NO MATCH: '{st}'")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    test_q_matching()
