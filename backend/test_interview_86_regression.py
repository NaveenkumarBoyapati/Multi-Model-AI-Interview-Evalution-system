# =====================================================================
# REGRESSION TEST SUITE FOR INTERVIEW #86 & PYTHON DEVELOPER EVALUATION
# =====================================================================

import os
import sys
import json

# Ensure backend root is on Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_connection
from question_bank import get_expected_concepts, CURATED_QUESTION_BANK, CONCEPT_SYNONYMS, generate_fallback_concepts
from evaluation import (
    is_concept_matched,
    evaluate_question,
    evaluate_interview,
    normalize_for_matching,
    local_evaluate,
    calculate_overall
)
from main import get_interview


def test_historical_interview_86_immutability():
    """Historical Interview #86 scores and records must remain strictly unchanged."""
    print("\n--- Test 1: Historical Interview #86 Immutability ---")
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, role, overall_score, technical_score, communication_score FROM Interviews WHERE id = 86")
    i86 = cur.fetchone()
    assert i86 is not None, "Interview #86 record missing from Interviews table"
    assert i86[1] == "Python Developer", f"Expected Python Developer, got {i86[1]}"
    assert i86[2] == 50.18, f"Historical overall_score changed: {i86[2]}"
    assert i86[3] == 48.12, f"Historical technical_score changed: {i86[3]}"
    assert i86[4] == 85.0, f"Historical communication_score changed: {i86[4]}"

    cur.execute("""
        SELECT question_number, overall_answer_score, matched_concepts, missing_concepts
        FROM InterviewAnswers
        WHERE interview_id = 86
        ORDER BY question_number
    """)
    answers = cur.fetchall()
    assert len(answers) == 3, f"Expected 3 answers for Interview #86, got {len(answers)}"

    # Q1 historical record
    assert answers[0][0] == 1
    assert answers[0][1] == 62.63, f"Historical Q1 score changed: {answers[0][1]}"
    assert json.loads(answers[0][2]) == ["education", "technical skills", "projects"], "Historical Q1 matched concepts altered"

    # Q2 historical record
    assert answers[1][0] == 2
    assert answers[1][1] == 40.88, f"Historical Q2 score changed: {answers[1][1]}"
    assert json.loads(answers[1][2]) == ["core strengths", "communication"], "Historical Q2 matched concepts altered"

    # Q3 historical record
    assert answers[2][0] == 3
    assert answers[2][1] == 0.0, f"Historical Q3 score changed: {answers[2][1]}"
    assert json.loads(answers[2][2]) == [], "Historical Q3 matched concepts altered"

    cur.close()
    conn.close()
    print("  >> PASSED: Historical Interview #86 is 100% immutable (scores: Q1=62.63, Q2=40.88, Q3=0.0, Overall=50.18)")


def test_prior_historical_interviews_immutability():
    """Verify Interviews #83, #80, #79, #76 are completely untouched."""
    print("\n--- Test 2: Prior Historical Interviews Immutability (#83, #80, #79, #76) ---")
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT overall_score FROM Interviews WHERE id = 83")
    r83 = cur.fetchone()
    if r83:
        assert r83[0] == 43.35, f"Interview #83 altered: {r83[0]}"

    cur.execute("SELECT overall_score FROM Interviews WHERE id = 80")
    r80 = cur.fetchone()
    if r80:
        assert r80[0] == 39.31, f"Interview #80 altered: {r80[0]}"

    cur.execute("SELECT overall_score FROM Interviews WHERE id = 79")
    r79 = cur.fetchone()
    if r79:
        assert r79[0] == 24.93, f"Interview #79 altered: {r79[0]}"

    cur.execute("SELECT overall_score FROM Interviews WHERE id = 76")
    r76 = cur.fetchone()
    if r76:
        assert r76[0] == 34.53, f"Interview #76 altered: {r76[0]}"

    cur.close()
    conn.close()
    print("  >> PASSED: Historical Interviews #83, #80, #79, and #76 scores remain identical.")


def test_python_developer_mro_expected_concepts():
    """Python Developer MRO question must return 5 rich expected concepts and not report empty."""
    print("\n--- Test 3: Python Developer MRO Expected Concepts Configuration ---")
    q_text = "What is MRO in Python?"
    concepts = get_expected_concepts(q_text, role="Python Developer")

    expected_set = [
        "method resolution order (mro)",
        "order in which python searches for methods and attributes",
        "multiple inheritance",
        "c3 linearization algorithm",
        "classname.mro() or classname.__mro__"
    ]

    assert concepts == expected_set, f"Expected {expected_set}, got {concepts}"

    # Also test without question mark and lowercase
    concepts_no_qm = get_expected_concepts("what is mro in python", role="Python Developer")
    assert concepts_no_qm == expected_set

    concepts_short = get_expected_concepts("what is mro?", role="Python Developer")
    assert concepts_short == expected_set

    # Also verify database Questions row 1845
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT expected_topics FROM Questions WHERE id = 1845")
    row = cur.fetchone()
    assert row is not None and row[0] is not None
    topics_in_db = [t.strip() for t in row[0].split(",") if t.strip()]
    assert topics_in_db == expected_set, f"DB expected_topics mismatch: {topics_in_db}"
    cur.close()
    conn.close()
    print(f"  >> PASSED: MRO expected concepts verified in both code repository and DB row 1845: {concepts}")


def test_get_interview_86_enriches_q3_expected_concepts():
    """get_interview(86) must provide expected concepts for Q3 so the result page has them."""
    print("\n--- Test 4: Result Page API (get_interview 86) Q3 Enrichment ---")
    data = get_interview(86)
    answers = data["answers"]
    assert len(answers) == 3

    q3_data = answers[2]
    assert q3_data["question_number"] == 3
    assert q3_data["expected_concepts"] == [
        "method resolution order (mro)",
        "order in which python searches for methods and attributes",
        "multiple inheritance",
        "c3 linearization algorithm",
        "classname.mro() or classname.__mro__"
    ]
    # Historical score must remain 0.0
    assert q3_data["overall_answer_score"] == 0.0

    # missing_concepts in returned JSON must contain all 5 concepts
    missing_list = json.loads(q3_data["missing_concepts"]) if isinstance(q3_data["missing_concepts"], str) else q3_data["missing_concepts"]
    assert len(missing_list) == 5, f"Expected 5 missing concepts, got {missing_list}"
    print("  >> PASSED: get_interview(86) returns 5 expected and missing concepts for Q3 without altering 0.0 score.")


def test_mro_full_answer_evaluation():
    """Complete technical explanation of MRO matches all 5 concepts and scores >90%."""
    print("\n--- Test 5: MRO Complete Answer Evaluation ---")
    ans_full = (
        "MRO stands for Method Resolution Order in Python. It defines the order in which Python "
        "searches for methods and attributes in a class hierarchy, especially with multiple inheritance. "
        "Python calculates this order using the C3 linearization algorithm. You can inspect the MRO "
        "using ClassName.mro() or the __mro__ attribute."
    )
    concepts = [
        "method resolution order (mro)",
        "order in which python searches for methods and attributes",
        "multiple inheritance",
        "c3 linearization algorithm",
        "classname.mro() or classname.__mro__"
    ]

    for c in concepts:
        assert is_concept_matched(c, ans_full), f"Concept '{c}' failed to match"

    res = evaluate_question("What is MRO in Python?", ans_full, concepts)
    assert res["technical_score"] == 100.0
    assert res["overall_score"] >= 90.0
    assert set(res["matched_concepts"]) == set(concepts)
    assert res["missing_concepts"] == []
    print(f"  >> PASSED: All 5 MRO concepts matched; Technical={res['technical_score']}%; Overall={res['overall_score']}%.")


def test_mro_partial_answer_evaluation():
    """Partial answer matches only covered concepts without false positives."""
    print("\n--- Test 6: MRO Partial Answer Evaluation ---")
    ans_partial = "MRO means method resolution order in Python, which helps resolve methods when using multiple inheritance."
    concepts = [
        "method resolution order (mro)",
        "order in which python searches for methods and attributes",
        "multiple inheritance",
        "c3 linearization algorithm",
        "classname.mro() or classname.__mro__"
    ]

    assert is_concept_matched("method resolution order (mro)", ans_partial)
    assert is_concept_matched("multiple inheritance", ans_partial)
    assert not is_concept_matched("c3 linearization algorithm", ans_partial)
    assert not is_concept_matched("classname.mro() or classname.__mro__", ans_partial)

    res = evaluate_question("What is MRO in Python?", ans_partial, concepts)
    assert "method resolution order (mro)" in res["matched_concepts"]
    assert "multiple inheritance" in res["matched_concepts"]
    assert "c3 linearization algorithm" in res["missing_concepts"]
    assert "classname.mro() or classname.__mro__" in res["missing_concepts"]
    assert 40.0 <= res["overall_score"] <= 60.0
    print(f"  >> PASSED: Partial answer matches only covered concepts; Overall={res['overall_score']}%.")


def test_mro_unrelated_answer_negative_test():
    """Unrelated answer must NOT receive concept credit."""
    print("\n--- Test 7: MRO Unrelated Answer Negative Test ---")
    unrelated = "I really enjoy building web scrapers with BeautifulSoup and saving data to SQLite."
    concepts = [
        "method resolution order (mro)",
        "order in which python searches for methods and attributes",
        "multiple inheritance",
        "c3 linearization algorithm",
        "classname.mro() or classname.__mro__"
    ]

    for c in concepts:
        assert not is_concept_matched(c, unrelated), f"Concept '{c}' incorrectly matched unrelated answer"

    res = evaluate_question("What is MRO in Python?", unrelated, concepts)
    assert res["technical_score"] == 0.0
    assert len(res["matched_concepts"]) == 0
    assert len(res["missing_concepts"]) == 5
    print("  >> PASSED: Unrelated answer matched 0 concepts with 0 technical score.")


def test_mro_unanswered_evaluation():
    """Unanswered question must score 0.0 with 0 matched concepts and all 5 missing concepts."""
    print("\n--- Test 8: MRO Unanswered Evaluation ---")
    concepts = [
        "method resolution order (mro)",
        "order in which python searches for methods and attributes",
        "multiple inheritance",
        "c3 linearization algorithm",
        "classname.mro() or classname.__mro__"
    ]
    res = evaluate_question("What is MRO in Python?", "", concepts)
    assert res["technical_score"] == 0.0
    assert res["overall_score"] == 0.0
    assert res["matched_concepts"] == []
    assert res["missing_concepts"] == concepts
    print("  >> PASSED: Unanswered MRO question scored 0.0 with 5 missing concepts.")


def test_other_curated_python_questions():
    """Verify other core Python questions return rich non-empty expected concepts."""
    print("\n--- Test 9: Core Curated Python Questions Integrity ---")
    core_questions = [
        "What is Python and what are its main features?",
        "What is the difference between a list and a tuple in Python?",
        "What are Python dictionaries and how are they used?",
        "Explain the concept of mutable and immutable objects in Python.",
        "What is the difference between == and is in Python?",
        "What are decorators in Python?",
        "What is list comprehension?",
        "What is a generator in Python?"
    ]

    for q in core_questions:
        concepts = get_expected_concepts(q, role="Python Developer")
        assert len(concepts) >= 3, f"Expected >=3 concepts for '{q}', got {concepts}"
    print(f"  >> PASSED: All {len(core_questions)} core Python questions have valid, rich concepts.")


def test_safe_fallback_for_unknown_questions():
    """
    Test fallback derivation for unknown / dynamically generated questions:
    - Must never return an empty list
    - Must extract key terms from the question
    - Must never invent unrelated concepts
    """
    print("\n--- Test 10: Safe Fallback for Unknown / Dynamic Questions ---")
    unknown_questions = [
        ("What is Celery in Python?", "Python Developer"),
        ("Explain Kafka consumer groups.", "Python Developer"),
        ("What is Docker containerization?", "Web Developer"),
        ("How does Kubernetes handle pod scheduling?", "Web Developer")
    ]

    for q, role in unknown_questions:
        concepts = get_expected_concepts(q, role=role)
        assert isinstance(concepts, list), f"Expected list for '{q}'"
        assert len(concepts) >= 3, f"Expected at least 3 concepts for '{q}', got {concepts}"
        # Ensure at least one concept contains the main technical term
        q_lower = q.lower()
        has_anchor = any(
            any(w in c.lower() for w in ["celery", "kafka", "docker", "kubernetes", "pod", "container"])
            for c in concepts
        )
        assert has_anchor, f"Fallback concepts for '{q}' lack question anchor: {concepts}"
    print("  >> PASSED: Dynamic/unknown questions safely derive anchored concepts without returning empty.")


def test_interview_score_consistency_with_unanswered():
    """
    Test 3-question Python Developer interview where Q3 (MRO) is unanswered:
    - Q1: Answered
    - Q2: Answered
    - Q3: Unanswered (MRO, 0.0)
    Verify:
    - Q3 overall score is 0.0.
    - Category averages represent answered questions.
    - No double-penalization of unanswered questions.
    """
    print("\n--- Test 11: 3-Question Python Developer Interview Score Consistency ---")
    q_data = [
        {
            "question_number": 1,
            "question": "Tell me about yourself.",
            "candidate_answer": "Hi, my name is Naveen Kumar. I am pursuing B.Tech final year in PPSU. I am an aspiring Python developer and have done projects using Python, SQL, and Power BI.",
            "is_answered": True,
            "expected_concepts": ["education", "technical skills", "projects", "relevant experience", "career goals"]
        },
        {
            "question_number": 2,
            "question": "What are your strengths and how can they help you in this role?",
            "candidate_answer": "My core strengths and technical skills are doing work on time and helping others. My communication is my key strength.",
            "is_answered": True,
            "expected_concepts": ["core strengths", "communication", "problem-solving", "practical example", "role contribution"]
        },
        {
            "question_number": 3,
            "question": "What is MRO in Python?",
            "candidate_answer": "",
            "is_answered": False,
            "expected_concepts": [
                "method resolution order (mro)",
                "order in which python searches for methods and attributes",
                "multiple inheritance",
                "c3 linearization algorithm",
                "classname.mro() or classname.__mro__"
            ]
        }
    ]

    res = evaluate_interview(q_data)
    qs = res["questions"]
    assert len(qs) == 3

    assert qs[0]["is_answered"] is True
    assert qs[0]["overall_score"] > 50.0

    assert qs[1]["is_answered"] is True
    assert qs[1]["matched_concepts"] == ["core strengths", "communication"]
    assert 35.0 <= qs[1]["overall_score"] <= 45.0

    assert qs[2]["is_answered"] is False
    assert qs[2]["overall_score"] == 0.0
    assert qs[2]["matched_concepts"] == []
    assert len(qs[2]["missing_concepts"]) == 5

    # Overall interview score reflects answered questions
    assert 45.0 <= res["overall_score"] <= 55.0
    assert res["technical_score"] > 0.0
    assert res["communication_score"] > 0.0
    print(f"  >> PASSED: Interview evaluated consistently (Overall={res['overall_score']}%, Tech={res['technical_score']}%, Comm={res['communication_score']}%), Q3 strictly 0.0 without double-penalizing.")


def run_all_tests():
    tests = [
        test_historical_interview_86_immutability,
        test_prior_historical_interviews_immutability,
        test_python_developer_mro_expected_concepts,
        test_get_interview_86_enriches_q3_expected_concepts,
        test_mro_full_answer_evaluation,
        test_mro_partial_answer_evaluation,
        test_mro_unrelated_answer_negative_test,
        test_mro_unanswered_evaluation,
        test_other_curated_python_questions,
        test_safe_fallback_for_unknown_questions,
        test_interview_score_consistency_with_unanswered
    ]

    passed = 0
    failed = 0

    print("=" * 70)
    print("STARTING REGRESSION TEST SUITE FOR INTERVIEW #86 & PYTHON DEVELOPER")
    print("=" * 70)

    for test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"  >> FAILED: {test_fn.__name__} - {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 70)
    print(f"TEST RESULTS: {passed} PASSED, {failed} FAILED (TOTAL {len(tests)})")
    print("=" * 70)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
