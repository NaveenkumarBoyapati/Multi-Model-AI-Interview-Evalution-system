import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from question_bank import CURATED_QUESTION_BANK, normalize_key
from main import get_connection

js_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "js", "interview.js")
with open(js_path, "r", encoding="utf-8") as f:
    text = f.read()

pattern = r'"([A-Za-z\s]+Developer|Data Analyst)":\s*\[(.*?)\]\s*(?:,|\n\s*\})'
roles_match = re.findall(pattern, text, re.DOTALL)

conn = get_connection()
cur = conn.cursor()
cur.execute("SELECT question_text, expected_topics FROM Questions WHERE expected_topics IS NOT NULL AND LTRIM(RTRIM(expected_topics)) <> ''")
db_questions = {normalize_key(r[0]): r[1] for r in cur.fetchall()}
conn.close()

curated_keys = {normalize_key(k) for k in CURATED_QUESTION_BANK.keys()}

print("--- Question Coverage Summary ---")
all_missing = {}
for role, q_block in roles_match:
    questions = re.findall(r'"([^"]+)"', q_block)
    covered_curated = 0
    covered_db = 0
    missing = []
    for q in questions:
        norm = normalize_key(q)
        in_c = norm in curated_keys
        in_d = norm in db_questions
        if in_c:
            covered_curated += 1
        if in_d:
            covered_db += 1
        if not in_c and not in_d:
            missing.append(q)
    print(f"Role: {role} ({len(questions)} total)")
    print(f"  In Curated Bank: {covered_curated}")
    print(f"  In DB Questions: {covered_db}")
    print(f"  Missing from BOTH: {len(missing)}")
    all_missing[role] = missing

for role, missing in all_missing.items():
    if missing:
        print(f"\nMissing for {role} ({len(missing)}):")
        for q in missing:
            print(f"  - {q}")
