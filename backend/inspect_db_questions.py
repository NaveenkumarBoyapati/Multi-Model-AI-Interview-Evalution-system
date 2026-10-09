import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from main import get_connection

conn = get_connection()
cur = conn.cursor()

print("--- Checking 'complex analysis' questions ---")
cur.execute("SELECT id, role_name, question_text, expected_topics FROM Questions WHERE question_text LIKE '%complex analysis%'")
rows = cur.fetchall()
print(f"Found {len(rows)} rows:")
for r in rows:
    print(f"  ID: {r[0]} | Role: {r[1]} | Q: {r[2]} | Expected: {r[3]}")

print("--- Checking 'complex analysis' questions ---")
cur.execute("SELECT a.id, a.question_id, a.question_number, a.question_text, q.expected_topics FROM InterviewAnswers a LEFT JOIN Questions q ON a.question_id = q.id WHERE a.interview_id = 94")
for a in cur.fetchall():
    print(f"  AnsID: {a[0]} | QID: {a[1]} | Q#: {a[2]} | Q: {a[3]} | ExpTopics: {a[4]}")

print("\n--- Checking for Questions with awkward fallback patterns in DB ---")
cur.execute("SELECT id, role_name, question_text, expected_topics FROM Questions WHERE expected_topics LIKE '%implementation%' AND expected_topics LIKE '%practical application%'")
fallback_rows = cur.fetchall()
print(f"Found {len(fallback_rows)} rows in Questions table with fallback patterns:")
for r in fallback_rows:
    print(f"  ID: {r[0]} | Role: {r[1]} | Q: {r[2]} | Topics: {r[3]}")

print("\n--- Checking for Questions with NULL or empty expected_topics ---")
cur.execute("SELECT id, role_name, question_text FROM Questions WHERE expected_topics IS NULL OR LTRIM(RTRIM(expected_topics)) = ''")
empty_rows = cur.fetchall()
print(f"Found {len(empty_rows)} empty rows:")
for r in empty_rows:
    print(f"  ID: {r[0]} | Role: {r[1]} | Q: {r[2]}")

