# =====================================================================
# REGRESSION TEST SUITE FOR INTERVIEW #83 & WEB DEVELOPER EVALUATION
# =====================================================================

import os
import sys
import json

# Ensure backend root is on Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_connection
from question_bank import get_expected_concepts, CURATED_QUESTION_BANK, CONCEPT_SYNONYMS
from evaluation import (
    is_concept_matched,
    evaluate_question,
    evaluate_interview,
    normalize_for_matching,
    local_evaluate,
    calculate_overall
)
from main import get_interview


def test_historical_interview_83_immutability():
    """Historical Interview #83 scores and records must remain strictly unchanged."""
    print("\n--- Test 1: Historical Interview #83 Immutability ---")
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, role, overall_score, technical_score, communication_score FROM Interviews WHERE id = 83")
    i83 = cur.fetchone()
    assert i83 is not None, "Interview #83 record missing from Interviews table"
    assert i83[1] == "Web Developer", f"Expected Web Developer, got {i83[1]}"
    assert i83[2] == 43.35, f"Historical overall_score changed: {i83[2]}"
    assert i83[3] == 40.16, f"Historical technical_score changed: {i83[3]}"
    assert i83[4] == 80.0, f"Historical communication_score changed: {i83[4]}"

    cur.execute("""
        SELECT question_number, overall_answer_score, matched_concepts, missing_concepts
        FROM InterviewAnswers
        WHERE interview_id = 83
        ORDER BY question_number
    """)
    answers = cur.fetchall()
    assert len(answers) == 3, f"Expected 3 answers for Interview #83, got {len(answers)}"

    # Q1 historical record
    assert answers[0][0] == 1
    assert answers[0][1] == 63.0, f"Historical Q1 score changed: {answers[0][1]}"
    assert json.loads(answers[0][2]) == ["education", "technical skills", "projects"], "Historical Q1 matched concepts altered"

    # Q2 historical record
    assert answers[1][0] == 2
    assert answers[1][1] == 26.86, f"Historical Q2 score changed: {answers[1][1]}"
    assert json.loads(answers[1][2]) == ["core strengths"], "Historical Q2 matched concepts altered"

    # Q3 historical record
    assert answers[2][0] == 3
    assert answers[2][1] == 0.0, f"Historical Q3 score changed: {answers[2][1]}"
    assert json.loads(answers[2][2]) == [], "Historical Q3 matched concepts altered"

    cur.close()
    conn.close()
    print("  >> PASSED: Historical Interview #83 is 100% immutable (scores: Q1=63.0, Q2=26.86, Q3=0.0, Overall=43.35)")


def test_prior_historical_interviews_immutability():
    """Verify Interviews #76, #79, #80 are completely untouched."""
    print("\n--- Test 2: Prior Historical Interviews Immutability (#76, #79, #80) ---")
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT overall_score FROM Interviews WHERE id = 76")
    r76 = cur.fetchone()
    if r76:
        assert r76[0] == 34.53, f"Interview #76 altered: {r76[0]}"

    cur.execute("SELECT overall_score FROM Interviews WHERE id = 79")
    r79 = cur.fetchone()
    if r79:
        assert r79[0] == 24.93, f"Interview #79 altered: {r79[0]}"

    cur.execute("SELECT overall_score FROM Interviews WHERE id = 80")
    r80 = cur.fetchone()
    if r80:
        assert r80[0] == 39.31, f"Interview #80 altered: {r80[0]}"

    cur.close()
    conn.close()
    print("  >> PASSED: Historical Interviews #76, #79, and #80 scores remain identical.")


def test_web_developer_q3_expected_concepts():
    """Web Developer Q3 must return 6 rich expected concepts and not report empty."""
    print("\n--- Test 3: Web Developer Q3 Expected Concepts Configuration ---")
    q_text = "What is responsive web design and media queries?"
    concepts = get_expected_concepts(q_text, role="Web Developer")

    expected_set = [
        "responsive web design",
        "media queries",
        "viewport",
        "breakpoints",
        "fluid layout and flexible images",
        "mobile-first design"
    ]

    assert concepts == expected_set, f"Expected {expected_set}, got {concepts}"

    concepts_no_qm = get_expected_concepts("What is responsive web design and media queries", role="Web Developer")
    assert concepts_no_qm == expected_set

    # Also verify database Questions row 1844
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT expected_topics FROM Questions WHERE id = 1844")
    row = cur.fetchone()
    assert row is not None and row[0] is not None
    topics_in_db = [t.strip() for t in row[0].split(",") if t.strip()]
    assert topics_in_db == expected_set, f"DB expected_topics mismatch: {topics_in_db}"
    cur.close()
    conn.close()
    print(f"  >> PASSED: Q3 expected concepts verified in both code repository and DB row 1844: {concepts}")


def test_get_interview_83_enriches_q3_expected_concepts():
    """get_interview(83) must provide expected concepts for Q3 so the result page has them."""
    print("\n--- Test 4: Result Page API (get_interview 83) Q3 Enrichment ---")
    data = get_interview(83)
    answers = data["answers"]
    assert len(answers) == 3

    q3_data = answers[2]
    assert q3_data["question_number"] == 3
    assert q3_data["expected_concepts"] == [
        "responsive web design",
        "media queries",
        "viewport",
        "breakpoints",
        "fluid layout and flexible images",
        "mobile-first design"
    ]
    # Historical score must remain 0.0
    assert q3_data["overall_answer_score"] == 0.0
    print("  >> PASSED: get_interview(83) returns 6 expected concepts for Q3 without altering 0.0 score.")


def test_q2_interview_83_candidate_answer_evaluation():
    """
    Test candidate's actual speech from Interview #83:
    'my core strengths and technical skills are doing work in on doing work on time and helping others core strengths technical skills communication communication, etc.'
    Must match:
    - 'core strengths' (doing work on time, helping others, core strengths)
    - 'communication' (communication communication)
    Must NOT match:
    - 'problem-solving'
    - 'practical example'
    - 'role contribution'
    Score must be moderate (~40%), NOT full marks.
    """
    print("\n--- Test 5: Interview #83 Q2 Candidate Speech Controlled Evaluation ---")
    ans2 = "my core strengths and technical skills are doing work in on doing work on time and helping others core strengths technical skills communication communication, etc."
    exp2 = ["core strengths", "communication", "problem-solving", "practical example", "role contribution"]

    assert is_concept_matched("core strengths", ans2), "'core strengths' must match"
    assert is_concept_matched("communication", ans2), "'communication' must match"
    assert not is_concept_matched("problem-solving", ans2), "'problem-solving' must NOT match"
    assert not is_concept_matched("practical example", ans2), "'practical example' must NOT match"
    assert not is_concept_matched("role contribution", ans2), "'role contribution' must NOT match"

    res = evaluate_question("What are your strengths and how can they help you in this role?", ans2, exp2)
    assert res["matched_concepts"] == ["core strengths", "communication"]
    assert res["missing_concepts"] == ["problem-solving", "practical example", "role contribution"]
    assert 35.0 <= res["overall_score"] <= 45.0, f"Expected 35-45%, got {res['overall_score']}"
    print(f"  >> PASSED: Candidate Q2 answer matches {res['matched_concepts']}; missing {res['missing_concepts']}; score={res['overall_score']}%.")


def test_strengths_punctuality_and_teamwork_matching():
    """Punctuality and teamwork/helping others must match 'core strengths'."""
    print("\n--- Test 6: Strengths Punctuality & Teamwork Synonym Matching ---")
    ans_punctual = "I take pride in my punctuality and always doing work on time to meet deadlines."
    assert is_concept_matched("core strengths", ans_punctual)

    ans_teamwork = "One of my greatest strengths is helping others and being a cooperative team player."
    assert is_concept_matched("core strengths", ans_teamwork)
    print("  >> PASSED: Punctuality and teamwork patterns successfully match core strengths.")


def test_strengths_communication_standalone_matching():
    """Standalone communication and variations must match 'communication'."""
    print("\n--- Test 7: Standalone Communication Matching ---")
    assert is_concept_matched("communication", "My primary strength is communication.")
    assert is_concept_matched("communication", "I excel at clear communication.")
    assert is_concept_matched("communication", "I am an effective communicator.")
    print("  >> PASSED: Standalone communication, adjective forms, and nouns matched.")


def test_practical_example_not_awarded_for_simple_lists():
    """A simple enumeration of tools using 'such as' must NOT award practical example credit."""
    print("\n--- Test 8: Practical Example Negative Test (No False Positives) ---")
    simple_list = "I have core strengths such as SQL, Python, Excel, and Power BI."
    assert not is_concept_matched("practical example", simple_list)
    print("  >> PASSED: Simple tool enumeration does not falsely award practical example.")


def test_strengths_thorough_answer_awards_high_score():
    """A thorough answer covering all 5 concepts with a practical example receives high marks."""
    print("\n--- Test 9: Strengths Complete Answer Evaluation ---")
    ans_full = (
        "My core strengths are problem-solving, punctuality, and clear communication. "
        "For example, in a recent web development project, our team faced a severe bug with responsiveness "
        "on mobile viewports. I analyzed the issue, identified the CSS media query breakpoint mismatch, "
        "and fixed the layout by using fluid units. This helped our team meet our release deadline, "
        "and I am confident these strengths will help me contribute effectively to your frontend team in this role."
    )
    exp = ["core strengths", "communication", "problem-solving", "practical example", "role contribution"]
    res = evaluate_question("What are your strengths and how can they help you in this role?", ans_full, exp)

    for c in exp:
        assert c in res["matched_concepts"], f"Expected {c} to match"
    assert len(res["missing_concepts"]) == 0
    assert res["overall_score"] >= 85.0
    print(f"  >> PASSED: Thorough answer matched all 5 concepts; scored {res['overall_score']}%.")


def test_speech_normalization_phonetics():
    """Verify common speech-recognition phonetic substitutions in evaluation logic."""
    print("\n--- Test 10: Speech Recognition Phonetic Normalization ---")
    raw = "I worked on paste agitization and multi-modally interview evolution system."
    norm = normalize_for_matching(raw)
    assert "pest digitization" in norm
    assert "multimodal interview evaluation" in norm
    print(f"  >> PASSED: Phonetic normalizations applied: '{raw}' -> '{norm}'")


def test_responsive_web_design_all_concepts_matched():
    """Verify all 6 responsive web design concepts match a complete, correct answer."""
    print("\n--- Test 11: Web Developer Q3 Full Answer Evaluation ---")
    ans_q3 = (
        "Responsive web design is an approach to web development where web pages adapt gracefully "
        "to different screen sizes and devices. It relies on the viewport meta tag to set the device width "
        "and initial scale. We use CSS media queries with breakpoints such as min-width and max-width "
        "to apply different layout rules. It also utilizes a fluid layout and flexible images using percentages, "
        "rem units, and max-width: 100%. Finally, modern responsive design follows a mobile-first design "
        "approach by designing for smaller viewports first and progressively enhancing for desktops."
    )
    concepts = [
        "responsive web design",
        "media queries",
        "viewport",
        "breakpoints",
        "fluid layout and flexible images",
        "mobile-first design"
    ]

    for c in concepts:
        assert is_concept_matched(c, ans_q3), f"Concept {c} failed to match"

    res = evaluate_question("What is responsive web design and media queries?", ans_q3, concepts)
    assert res["technical_score"] == 100.0
    assert res["overall_score"] >= 90.0
    assert set(res["matched_concepts"]) == set(concepts)
    assert res["missing_concepts"] == []
    print(f"  >> PASSED: All 6 concepts matched; Technical={res['technical_score']}%; Overall={res['overall_score']}%.")


def test_responsive_web_design_unanswered():
    """Unanswered Q3 must receive strictly 0.0 with 0 matched concepts and all 6 missing concepts."""
    print("\n--- Test 12: Web Developer Q3 Unanswered Evaluation ---")
    concepts = [
        "responsive web design",
        "media queries",
        "viewport",
        "breakpoints",
        "fluid layout and flexible images",
        "mobile-first design"
    ]
    res = evaluate_question("What is responsive web design and media queries?", "", concepts)
    assert res["technical_score"] == 0.0
    assert res["overall_score"] == 0.0
    assert res["matched_concepts"] == []
    assert res["missing_concepts"] == concepts
    print("  >> PASSED: Unanswered Q3 scored 0.0 with 0 matched and 6 missing concepts.")


def test_interview_evaluation_score_consistency():
    """
    Test a 3-question interview evaluation where Q3 is unanswered:
    - Q1: Answered (e.g., 63.0)
    - Q2: Answered (e.g., 39.88)
    - Q3: Unanswered (0.0)
    Verify:
    - Q3 overall score is 0.0.
    - Category averages represent answered questions.
    - No double-penalization of unanswered questions.
    """
    print("\n--- Test 13: 3-Question Web Developer Interview Score Consistency ---")
    q_data = [
        {
            "question_number": 1,
            "question": "Tell me about yourself.",
            "candidate_answer": "Hi, my name is Navin Kumar. I am pursuing B.Tech final year. I have worked on projects using SQL, Excel, and Power BI.",
            "is_answered": True,
            "expected_concepts": ["education", "technical skills", "projects", "relevant experience", "career goals"]
        },
        {
            "question_number": 2,
            "question": "What are your strengths and how can they help you in this role?",
            "candidate_answer": "my core strengths and technical skills are doing work in on doing work on time and helping others core strengths technical skills communication communication, etc.",
            "is_answered": True,
            "expected_concepts": ["core strengths", "communication", "problem-solving", "practical example", "role contribution"]
        },
        {
            "question_number": 3,
            "question": "What is responsive web design and media queries?",
            "candidate_answer": "",
            "is_answered": False,
            "expected_concepts": ["responsive web design", "media queries", "viewport", "breakpoints", "fluid layout and flexible images", "mobile-first design"]
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
    assert len(qs[2]["missing_concepts"]) == 6

    # Overall interview score must be between 40 and 55, reflecting the answered questions
    assert 40.0 <= res["overall_score"] <= 55.0
    assert res["technical_score"] > 0.0
    assert res["communication_score"] > 0.0
    print(f"  >> PASSED: Interview evaluated consistently (Overall={res['overall_score']}%, Tech={res['technical_score']}%, Comm={res['communication_score']}%), Q3 strictly 0.0 without double-penalizing.")


def run_all_tests():
    tests = [
        test_historical_interview_83_immutability,
        test_prior_historical_interviews_immutability,
        test_web_developer_q3_expected_concepts,
        test_get_interview_83_enriches_q3_expected_concepts,
        test_q2_interview_83_candidate_answer_evaluation,
        test_strengths_punctuality_and_teamwork_matching,
        test_strengths_communication_standalone_matching,
        test_practical_example_not_awarded_for_simple_lists,
        test_strengths_thorough_answer_awards_high_score,
        test_speech_normalization_phonetics,
        test_responsive_web_design_all_concepts_matched,
        test_responsive_web_design_unanswered,
        test_interview_evaluation_score_consistency
    ]

    passed = 0
    failed = 0

    print("=" * 70)
    print("STARTING REGRESSION TEST SUITE FOR INTERVIEW #83 & WEB DEVELOPER")
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
