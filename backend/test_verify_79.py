import sys
from main import get_interview

res = get_interview(79)
print(f"Interview ID: 79 | Role: {res['interview']['role']}")
print(f"Interview overall: {res['interview']['overall_score']}")
print(f"Evaluation overall: {res['evaluation']['overall_score']}")
print(f"Category scores - Tech: {res['evaluation']['technical_score']}, Rel: {res['evaluation']['relevance_score']}, Comm: {res['evaluation']['communication_score']}, Conf: {res['evaluation']['confidence_score']}, Prob: {res['evaluation']['problem_solving_score']}")

for a in res['answers']:
    q_num = a['question_number']
    q_text = a['question_text']
    ans = a.get('answer_text')
    exp = a['expected_concepts']
    mat = a['matched_concepts']
    cs = a['concept_score']
    ps = a.get('problem_solving_score')
    os = a.get('overall_answer_score')
    print(f"\nQ{q_num}: {q_text}")
    print(f"  Answer: {ans}")
    print(f"  Expected Concepts: {exp}")
    print(f"  Matched Concepts: {mat}")
    print(f"  Concept Score: {cs}")
    print(f"  Problem Solving Score: {ps}")
    print(f"  Question Overall: {os}")

# Assert Interview #79 historical scores are NOT modified
assert res['interview']['overall_score'] == 24.93
assert res['evaluation']['overall_score'] == 24.93
assert res['answers'][0]['overall_answer_score'] == 27.5
assert res['answers'][1]['overall_answer_score'] == 22.36
assert res['answers'][2]['overall_answer_score'] == 0.0

# Assert Q3 now has expected concepts defined (not empty)
assert len(res['answers'][2]['expected_concepts']) == 5
assert "java unit testing framework" in res['answers'][2]['expected_concepts']

print("\n>> All Interview #79 checks passed: Historical scores intact & Q3 expected concepts verified!")
