import re
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from question_bank import get_expected_concepts
from database import get_connection

js_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "js", "interview.js")
with open(js_path, "r", encoding="utf-8") as f:
    js_text = f.read()

# Match each role block in roleQuestions
pattern = r'"([A-Za-z\s]+Developer|Data Analyst)":\s*\[(.*?)\]\s*(?:,|\n\s*\})'
roles_match = re.findall(pattern, js_text, re.DOTALL)
print(f"Found {len(roles_match)} roles in JS: {[r[0] for r in roles_match]}")

conn = get_connection()
cur = conn.cursor()

total_audit_questions = 0
total_empty_concepts = 0

for role, q_block in roles_match:
    questions = re.findall(r'"([^"]+)"', q_block)
    total_audit_questions += len(questions)
    print(f"\n========================================================")
    print(f"Auditing Role: {role} ({len(questions)} questions in interview.js)")
    print(f"========================================================")
    empty_concepts = []
    missing_in_db = []
    
    for q in questions:
        c = get_expected_concepts(q, role=role)
        if not c:
            empty_concepts.append(q)
            
        cur.execute("SELECT expected_topics FROM Questions WHERE LOWER(LTRIM(RTRIM(question_text))) = LOWER(?)", (q.strip(),))
        row = cur.fetchone()
        if not row or not row[0] or not str(row[0]).strip():
            missing_in_db.append(q)
            
    total_empty_concepts += len(empty_concepts)
    print(f"Questions with EMPTY get_expected_concepts(): {len(empty_concepts)}")
    for eq in empty_concepts:
        print(f"  [EMPTY] {eq}")
        
    print(f"Questions missing or empty in DB Questions table: {len(missing_in_db)}")
    for mq in missing_in_db:
        print(f"  [MISSING IN DB] {mq}")

print(f"\nAUDIT SUMMARY: {total_audit_questions} questions checked, {total_empty_concepts} currently have empty expected concepts.")
cur.close()
conn.close()
