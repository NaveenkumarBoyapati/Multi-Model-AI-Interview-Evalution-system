from main import get_interview
import json

res = get_interview(80)
print(f"Interview ID: 80 | Role: {res['interview']['role']}")
print(f"Interview overall: {res['interview']['overall_score']}")
print(f"Evaluation overall: {res['evaluation']['overall_score']}")
print(f"Category scores - Tech: {res['evaluation']['technical_score']}, Rel: {res['evaluation']['relevance_score']}, Comm: {res['evaluation']['communication_score']}, Conf: {res['evaluation']['confidence_score']}, Prob: {res['evaluation']['problem_solving_score']}")

for a in res['answers']:
    print("\n" + "="*50)
    print(f"Q{a['question_number']}: {a['question_text']}")
    print(f"  Answer: {a.get('answer_text')}")
    print(f"  Expected Concepts: {a.get('expected_concepts')}")
    print(f"  Matched Concepts: {a.get('matched_concepts')}")
    print(f"  Concept Score: {a.get('concept_score')}")
    print(f"  Technical Score: {a.get('technical_score')}")
    print(f"  Relevance Score: {a.get('relevance_score')}")
    print(f"  Communication Score: {a.get('communication_score')}")
    print(f"  Confidence Score: {a.get('confidence_score')}")
    print(f"  Problem Solving Score: {a.get('problem_solving_score')}")
    print(f"  Overall Answer Score: {a.get('overall_answer_score')}")
