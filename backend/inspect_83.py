from main import get_interview
import json
from database import get_connection

res = get_interview(83)
print(f"Interview ID: 83 | Role: {res['interview']['role']}")
print(f"Interview overall: {res['interview']['overall_score']}")
print(f"Evaluation overall: {res['evaluation']['overall_score']}")
print(f"Category scores - Tech: {res['evaluation']['technical_score']}, Rel: {res['evaluation']['relevance_score']}, Comm: {res['evaluation']['communication_score']}, Conf: {res['evaluation']['confidence_score']}, Prob: {res['evaluation']['problem_solving_score']}")

for a in res['answers']:
    print("\n" + "="*50)
    print(f"Q{a['question_number']}: {a['question_text']}")
    print(f"  Question ID: {a.get('question_id')}")
    print(f"  Answer: {a.get('answer_text')}")
    print(f"  Expected Concepts: {a.get('expected_concepts')}")
    print(f"  Matched Concepts: {a.get('matched_concepts')}")
    print(f"  Missing Concepts: {a.get('missing_concepts')}")
    print(f"  Concept Score: {a.get('concept_score')}")
    print(f"  Technical Score: {a.get('technical_score')}")
    print(f"  Relevance Score: {a.get('relevance_score')}")
    print(f"  Communication Score: {a.get('communication_score')}")
    print(f"  Confidence Score: {a.get('confidence_score')}")
    print(f"  Problem Solving Score: {a.get('problem_solving_score')}")
    print(f"  Overall Answer Score: {a.get('overall_answer_score')}")

conn = get_connection()
cur = conn.cursor()
cur.execute("SELECT id, interview_id, question_id, question_number, question_text, category, matched_concepts, missing_concepts, overall_answer_score FROM InterviewAnswers WHERE interview_id=83 ORDER BY question_number")
print("\n" + "="*50 + "\nDB ROWS in InterviewAnswers:")
for row in cur.fetchall():
    print(" ", row)

print("\n" + "="*50 + "\nFULL TRANSCRIPT:")
print(res['interview'].get('transcript'))
cur.close()
conn.close()
