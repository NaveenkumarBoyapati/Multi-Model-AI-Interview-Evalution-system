import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import get_interview
from evaluation import (
    evaluate_question,
    evaluate_interview,
    is_concept_matched,
    is_self_introduction,
    is_strengths_question,
    calculate_overall
)
from question_bank import get_expected_concepts, CURATED_QUESTION_BANK
from database import get_connection


def run_tests():
    print("=" * 70)
    print("RUNNING DATA ANALYST & INTERVIEW #80 EVALUATION TEST SUITE")
    print("=" * 70)

    # -------------------------------------------------------------
    # TEST 1: Historical Interview #80 Database & Score Integrity
    # -------------------------------------------------------------
    print("\n--- [Test 1] Historical Interview #80 Integrity Check ---")
    res80 = get_interview(80)
    assert res80["status"] == "success", "Failed to retrieve Interview #80"

    inv = res80["interview"]
    ev = res80["evaluation"]
    ans = res80["answers"]

    print(f"  Interview ID: {inv['id']} | Role: {inv['role']}")
    print(f"  Stored Overall Score: {inv['overall_score']}")
    print(f"  Stored Evaluation Score: {ev['overall_score']}")
    print(f"  Stored Q1 Score: {ans[0]['overall_answer_score']}")
    print(f"  Stored Q2 Score: {ans[1]['overall_answer_score']}")
    print(f"  Stored Q3 Score: {ans[2]['overall_answer_score']}")

    # Historical scores MUST NOT BE CHANGED
    assert inv["overall_score"] == 39.31, f"Historical overall_score changed: {inv['overall_score']}"
    assert ev["overall_score"] == 39.31, f"Historical evaluation score changed: {ev['overall_score']}"
    assert ans[0]["overall_answer_score"] == 62.63, f"Historical Q1 score changed: {ans[0]['overall_answer_score']}"
    assert ans[1]["overall_answer_score"] == 19.12, f"Historical Q2 score changed: {ans[1]['overall_answer_score']}"
    assert ans[2]["overall_answer_score"] == 0.0, f"Historical Q3 score changed: {ans[2]['overall_answer_score']}"

    # Historical stored matched_concepts in DB rows must not be altered
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT question_number, matched_concepts, overall_answer_score FROM InterviewAnswers WHERE interview_id = 80 ORDER BY question_number")
    db_answers = cur.fetchall()
    cur.close()
    conn.close()

    assert db_answers[0][1] == '["education", "technical skills", "projects"]', "Historical Q1 matched concepts altered in DB!"
    assert db_answers[1][1] == '["core strengths"]', "Historical Q2 matched concepts altered in DB!"
    assert db_answers[2][1] == '[]', "Historical Q3 matched concepts altered in DB!"
    print("  >> Stored database rows for Interview #80 remain completely untouched.")

    # Q3 Expected Concepts enrichment verification
    q3_exp = ans[2]["expected_concepts"]
    print(f"  Q3 Expected Concepts enriched in response: {q3_exp}")
    assert len(q3_exp) == 6, f"Expected 6 concepts for Q3, got {len(q3_exp)}"
    assert "examining dataset structure" in q3_exp
    assert "data types" in q3_exp
    assert "missing values" in q3_exp
    assert "duplicates" in q3_exp
    assert "distributions" in q3_exp
    assert "quality issues" in q3_exp
    print(">> Test 1 PASSED: Historical Interview #80 intact & Q3 concepts enriched!")

    # -------------------------------------------------------------
    # TEST 2: Concept-Matching Pipeline & Synonym Normalization
    # -------------------------------------------------------------
    print("\n--- [Test 2] Concept Matching & Synonym Normalization ---")
    q2_text = "What are your strengths and how can they help you in this role?"
    q2_ans = (
        "And my core strength and technical skills are Being loyal to the company "
        "and doing work assigned by the company and problem solver, quick problem solver "
        "and most important strength is mind being consistent."
    )
    exp2 = get_expected_concepts(q2_text)

    # Verification of concepts on Interview 80 Q2 answer
    assert is_concept_matched("core strengths", q2_ans), "'core strengths' must match"
    assert is_concept_matched("problem-solving", q2_ans), "'problem-solving' must match for 'problem solver'"
    assert is_concept_matched("problem solving", q2_ans), "'problem solving' must match"
    assert not is_concept_matched("communication", q2_ans), "'communication' should not match"
    assert not is_concept_matched("practical example", q2_ans), "'practical example' should not match"
    assert not is_concept_matched("role contribution", q2_ans), "'role contribution' should not match"
    print("  Interview #80 Q2 answer correctly matches 'core strengths' and 'problem-solving'")
    print("  and keeps 'communication', 'practical example', and 'role contribution' separate.")

    # Test "consistency" and "loyalty" as core strengths
    strength_ans_1 = "My greatest strengths are loyalty to my organization and consistency in high quality work."
    assert is_concept_matched("core strengths", strength_ans_1), "loyalty and consistency must match core strengths"
    assert not is_concept_matched("practical example", strength_ans_1), "loyalty and consistency must NOT match practical example"
    assert not is_concept_matched("role contribution", strength_ans_1), "loyalty and consistency must NOT match role contribution"

    strength_ans_2 = "Being consistent and being loyal."
    assert is_concept_matched("core strengths", strength_ans_2), "'Being consistent and being loyal' must match core strengths"
    print("  >> 'consistency' and 'loyalty' count as core strengths without inflating other concepts.")

    # Test problem solver phrase variants
    prob_variants = [
        ("I am a natural problem solver in data analysis.", True),
        ("She is a quick problem solver when tackling production issues.", True),
        ("I enjoy solving problems using SQL and Python.", True),
        ("Troubleshooting data pipelines is my strength.", True),
        ("Analytical thinking helps me identify bugs quickly.", True),
        ("I love to walk in the park and read general fiction.", False),
        ("Doing hard work and showing up every single day.", False)
    ]
    for phrase, expected in prob_variants:
        res = is_concept_matched("problem-solving", phrase)
        assert res == expected, f"Failed for '{phrase}': expected {expected}, got {res}"
    print("  >> Problem solver phrase variants verified with zero false positives.")
    print(">> Test 2 PASSED: Concept matching and normalization robust!")

    # -------------------------------------------------------------
    # TEST 3: Data Profiling Expected Concepts & Matching
    # -------------------------------------------------------------
    print("\n--- [Test 3] Data Profiling Expected Concepts & Matching ---")
    q3_text = "What is data profiling?"
    exp3 = get_expected_concepts(q3_text, role="Data Analyst")
    print("  Expected concepts for 'What is data profiling?':", exp3)
    assert len(exp3) == 6
    expected_set = {
        "examining dataset structure",
        "data types",
        "missing values",
        "duplicates",
        "distributions",
        "quality issues"
    }
    assert set(exp3) == expected_set, f"Concept mismatch: {set(exp3)} != {expected_set}"

    full_profiling_ans = (
        "Data profiling is the foundational process of examining dataset structure and schemas, "
        "inspecting column data types, identifying missing values or null counts, detecting duplicate rows, "
        "analyzing statistical distributions and frequencies, and uncovering data quality issues or anomalies."
    )
    for c in exp3:
        matched = is_concept_matched(c, full_profiling_ans)
        assert matched, f"Concept '{c}' failed to match full profiling answer"
    print("  >> Full profiling answer matched all 6 expected concepts.")

    partial_profiling_ans = "Data profiling is checking the table schema structure and looking for missing values."
    assert is_concept_matched("examining dataset structure", partial_profiling_ans)
    assert is_concept_matched("missing values", partial_profiling_ans)
    assert not is_concept_matched("duplicates", partial_profiling_ans)
    assert not is_concept_matched("distributions", partial_profiling_ans)
    print("  >> Partial profiling answer matched only relevant concepts (no score inflation).")
    print(">> Test 3 PASSED: Data profiling concepts verified!")

    # -------------------------------------------------------------
    # TEST 4: Problem Solving Rubric Audit by Question Type
    # -------------------------------------------------------------
    print("\n--- [Test 4] Problem Solving Rubric by Question Type ---")
    # A. Self-introduction without problem-solving evidence -> None (Not Available)
    intro_res = evaluate_question(
        "Tell me about yourself.",
        candidate_answer="Hi, my name is Naveen. I am a final-year B.Tech student passionate about data analytics.",
        expected_concepts=get_expected_concepts("Tell me about yourself."),
        category="Introduction"
    )
    print("  Self-intro Problem Solving:", intro_res["problem_solving_score"])
    assert intro_res["problem_solving_score"] is None, "Self-introduction should be None (Not Available)"

    # B. Strengths question with explicit problem solver mention (Interview 80 Q2 answer)
    q2_evaluated = evaluate_question(
        q2_text,
        candidate_answer=q2_ans,
        expected_concepts=exp2,
        category="HR"
    )
    print("  Strengths with 'problem solver' Problem Solving Score:", q2_evaluated["problem_solving_score"])
    print("  Strengths Overall Score:", q2_evaluated["overall_score"])
    assert q2_evaluated["problem_solving_score"] >= 45.0, (
        f"Problem solving score should evaluate evidence, got {q2_evaluated['problem_solving_score']}"
    )
    assert q2_evaluated["overall_score"] > 35.0, (
        f"Overall score for Q2 answer should reflect actual evidence, got {q2_evaluated['overall_score']}"
    )

    # C. Incomplete strengths question with NO problem-solving mention
    q2_inc = evaluate_question(
        q2_text,
        candidate_answer="my core strengths and technical skills are doing hard work.",
        expected_concepts=exp2,
        category="HR"
    )
    print("  Incomplete Strengths without problem solving:", q2_inc["problem_solving_score"])
    assert q2_inc["problem_solving_score"] == 0.0, "Answer without problem solving evidence should score 0.0"

    # D. Strengths question with full STAR problem-solving example
    q2_star = evaluate_question(
        q2_text,
        candidate_answer=(
            "My main strength is problem solving and analytical troubleshooting. "
            "For example, in my university project, when the pipeline failed because of memory bottlenecks, "
            "I analyzed the root cause, optimized the SQL query, and successfully resolved the issue."
        ),
        expected_concepts=exp2,
        category="HR"
    )
    print("  Strengths with STAR example Problem Solving Score:", q2_star["problem_solving_score"])
    assert q2_star["problem_solving_score"] >= 80.0, "Full STAR example should receive high problem solving score"
    print(">> Test 4 PASSED: Problem solving rubric differentiates question types and evidence properly!")

    # -------------------------------------------------------------
    # TEST 5: Scoring Formula Consistency & No Misleading 0%
    # -------------------------------------------------------------
    print("\n--- [Test 5] Consistent Formulas & No Misleading 0% ---")
    # Verify that when problem_solving_score is None, calculate_overall scales weights correctly
    ov_with_none = calculate_overall(80.0, 80.0, 80.0, 80.0, 80.0, 80.0, None)
    assert ov_with_none == 80.0, f"Expected 80.0, got {ov_with_none}"

    ov_with_zero = calculate_overall(80.0, 80.0, 80.0, 80.0, 80.0, 80.0, 0.0)
    assert ov_with_zero == 76.0, f"Expected 76.0 (5% penalty), got {ov_with_zero}"

    # Verify that questions with no expected concepts defined don't cause misleading 0%
    no_concept_q = evaluate_question(
        "Can you share any additional thoughts?",
        candidate_answer="I am excited about this opportunity and ready to start immediately.",
        expected_concepts=[],
        category="HR"
    )
    assert no_concept_q["concept_score"] is None, "When concepts are not defined, concept_score should be None"
    assert no_concept_q["overall_score"] > 0, "Question with undefined concepts should not be forced to 0"
    print(">> Test 5 PASSED: Scoring formula handles None and active weights consistently!")

    # -------------------------------------------------------------
    # TEST 6: Fresh End-to-End Data Analyst Interview Evaluation
    # -------------------------------------------------------------
    print("\n--- [Test 6] Fresh End-to-End Data Analyst Interview Evaluation ---")
    mock_interview = [
        {
            "question_number": 1,
            "question": "Tell me about yourself.",
            "candidate_answer": (
                "Hi, my name is Naveen Kumar. I am pursuing B.Tech at P.P. Savani University. "
                "I am passionate about data analysis and have built projects in Python, SQL, and Power BI."
            ),
            "expected_concepts": get_expected_concepts("Tell me about yourself."),
            "category": "Introduction",
            "is_answered": True
        },
        {
            "question_number": 2,
            "question": "What are your strengths and how can they help you in this role?",
            "candidate_answer": (
                "My core strengths are Being loyal to the company and quick problem solver and being consistent."
            ),
            "expected_concepts": get_expected_concepts("What are your strengths and how can they help you in this role?"),
            "category": "HR",
            "is_answered": True
        },
        {
            "question_number": 3,
            "question": "What is data profiling?",
            "candidate_answer": (
                "Data profiling is examining dataset structure, analyzing data types, finding missing values and nulls, "
                "identifying duplicates, assessing distributions, and detecting data quality issues."
            ),
            "expected_concepts": get_expected_concepts("What is data profiling?", role="Data Analyst"),
            "category": "Technical",
            "is_answered": True
        }
    ]

    eval_out = evaluate_interview(mock_interview)

    print("\nFresh Interview Results:")
    print(f"  Overall Score: {eval_out['overall_score']}")
    print(f"  Technical: {eval_out['technical_score']}")
    print(f"  Relevance: {eval_out['relevance_score']}")
    print(f"  Concepts: {eval_out['concept_score']}")
    print(f"  Communication: {eval_out['communication_score']}")
    print(f"  Confidence: {eval_out['confidence_score']}")
    print(f"  Problem Solving: {eval_out['problem_solving_score']}")

    q1_out = eval_out["questions"][0]
    q2_out = eval_out["questions"][1]
    q3_out = eval_out["questions"][2]

    print("\nQuestion Breakdown:")
    print(f"  Q1: Matched={q1_out['matched_concepts']} | Prob={q1_out['problem_solving_score']} | Overall={q1_out['overall_score']}")
    print(f"  Q2: Matched={q2_out['matched_concepts']} | Prob={q2_out['problem_solving_score']} | Overall={q2_out['overall_score']}")
    print(f"  Q3: Matched={q3_out['matched_concepts']} | Prob={q3_out['problem_solving_score']} | Overall={q3_out['overall_score']}")

    # Assertions on Fresh Interview:
    assert "education" in q1_out["matched_concepts"]
    assert "technical skills" in q1_out["matched_concepts"]
    assert "projects" in q1_out["matched_concepts"]
    assert q1_out["problem_solving_score"] is None, "Q1 should be None (Not Available)"

    assert "core strengths" in q2_out["matched_concepts"]
    assert "problem-solving" in q2_out["matched_concepts"]
    assert q2_out["problem_solving_score"] >= 45.0, "Q2 should evaluate problem solver evidence"
    assert q2_out["overall_score"] > 35.0

    assert len(q3_out["matched_concepts"]) == 6, f"Q3 should match all 6 concepts, got {len(q3_out['matched_concepts'])}"
    assert q3_out["overall_score"] >= 85.0

    # Interview overall must be balanced and strong (around 60-75)
    assert 60.0 <= eval_out["overall_score"] <= 80.0, f"Expected balanced overall score, got {eval_out['overall_score']}"
    # Problem solving at interview level should average only answered questions that test it (Q2 and Q3)
    assert eval_out["problem_solving_score"] is not None and eval_out["problem_solving_score"] > 0
    print(">> Test 6 PASSED: Fresh end-to-end Data Analyst interview evaluated successfully!")

    print("\n" + "=" * 70)
    print("ALL DATA ANALYST & INTERVIEW #80 TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
