import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_connection

def update_mro_question():
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT id, role_name, question_text, expected_topics FROM Questions WHERE id = 1845")
    before = cur.fetchone()
    print("Found row before update:")
    print(" ", before)
    
    topics = "method resolution order (mro), order in which python searches for methods and attributes, multiple inheritance, c3 linearization algorithm, classname.mro() or classname.__mro__"
    
    cur.execute("""
        UPDATE Questions
        SET expected_topics = ?
        WHERE id = 1845
    """, (topics,))
    conn.commit()
    
    cur.execute("SELECT id, role_name, question_text, expected_topics FROM Questions WHERE id = 1845")
    after = cur.fetchone()
    print("\nFound row after update:")
    print(" ", after)
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    update_mro_question()
