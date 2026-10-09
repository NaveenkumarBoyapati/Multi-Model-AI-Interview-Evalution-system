"""
System-Wide Regression Test Suite
Validates:
1. Every role's question bank and expected concepts (Python, Java, Data Analyst, Web Developer).
2. Data Analyst question: "How would you explain a complex analysis to a non-technical person?"
   - Exact 5 concepts present
   - Full answer evaluation (100% tech score, all 5 matched)
   - Partial answer evaluation (only covered concepts credited)
   - Unrelated answer evaluation (0 concepts matched, 0 tech score)
   - Unanswered evaluation (0 score, all 5 missing)
3. MRO question regression (Interview #86 fix intact).
4. Responsive Web Design question regression (Interview #83 fix intact).
5. Data Profiling question regression (Interview #80 fix intact).
6. Speech recognition phonetic normalization ("Tableau" / "Diablo" / "Data Blue", "my skills are", "i did projects").
7. Evidence-based feedback: no ungrounded "Communication was clear" on short/low-relevance answers.
8. Unknown-question safe fallback quality: no awkward "implementation" templates; logs configuration warning.
9. Historical data immutability: Interviews #94, #86, #83, #80, #79, #76 remain completely unmodified.
10. Fresh end-to-end interview evaluation, SQL Server persistence, and API retrieval.
"""

import sys
import os
import json
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from question_bank import (
    get_expected_concepts,
    generate_fallback_concepts,
    CURATED_QUESTION_BANK,
    CONCEPT_SYNONYMS
)
from evaluation import (
    evaluate_question,
    evaluate_interview,
    is_concept_matched,
    normalize_for_matching
)
from transcription import get_initial_prompt
from main import get_interview, save_interview_record, get_connection


def test_1_all_roles_question_coverage():
    """Verify all questions across all 4 frontend roles have curated concepts and 0 are empty."""
    print("\n--- Test 1: All Roles Question Coverage Audit ---")
    js_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "js", "interview.js")
    with open(js_path, "r", encoding="utf-8") as f:
        js_text = f.read()

    pattern = r'"([A-Za-z\s]+Developer|Data Analyst)":\s*\[(.*?)\]\s*(?:,|\n\s*\})'
    roles_match = re.findall(pattern, js_text, re.DOTALL)
    assert len(roles_match) >= 4, f"Expected at least 4 roles in interview.js, found {len(roles_match)}"

    total_questions = 0
    for role, q_block in roles_match:
        questions = re.findall(r'"([^"]+)"', q_block)
        total_questions += len(questions)
        for q in questions:
            concepts = get_expected_concepts(q, role=role)
            assert concepts and len(concepts) >= 3, f"Empty or too few concepts for '{q}' (role={role})"
            # Ensure none have awkward joined implementation phrasing
            for c in concepts:
                assert "and analysis implementation" not in c, f"Awkward concept in '{q}': {c}"

    print(f"  >> PASSED: All {total_questions} questions across all 4 roles have verified non-empty, clean concepts.")


def test_2_complex_analysis_expected_concepts():
    """Verify the 5 specified concepts for 'How would you explain a complex analysis to a non-technical person?'."""
    print("\n--- Test 2: Complex Analysis Question Curated Concepts ---")
    q = "How would you explain a complex analysis to a non-technical person?"
    concepts = get_expected_concepts(q, role="Data Analyst")

    expected_5 = [
        "simplify complex technical information",
        "use non-technical language and avoid jargon",
        "explain key findings clearly",
        "provide a relatable example",
        "connect findings to practical or business impact"
    ]
    assert len(concepts) == 5, f"Expected 5 concepts, got {len(concepts)}: {concepts}"
    for exp in expected_5:
        assert exp in concepts, f"Expected '{exp}' in concepts, got: {concepts}"

    print(f"  >> PASSED: All 5 curated concepts present for '{q}'.")


def test_3_complex_analysis_full_answer():
    """Verify full, thorough answer matches all 5 concepts and receives high score."""
    print("\n--- Test 3: Complex Analysis Full Answer Evaluation ---")
    q = "How would you explain a complex analysis to a non-technical person?"
    ans = (
        "When explaining complex analysis to a non-technical stakeholder, my first step is to simplify complex "
        "technical information by breaking it down into easily digestible concepts. I deliberately use non-technical "
        "language and avoid jargon so that everyone feels comfortable and engaged. I focus on explaining key findings "
        "clearly, emphasizing what the data shows rather than getting lost in mathematical details. To make it memorable, "
        "I provide a relatable example and use an analogy, such as comparing our customer churn funnel to a leaky bucket. "
        "Finally, I connect findings directly to business impact by highlighting actionable recommendations that drive "
        "strategic decision-making and revenue growth."
    )
    res = evaluate_question(q, candidate_answer=ans, expected_concepts=get_expected_concepts(q, role="Data Analyst"))
    assert len(res["matched_concepts"]) == 5, f"Expected 5 matches, got: {res['matched_concepts']}"
    assert res["technical_score"] >= 95.0
    assert res["overall_score"] >= 88.0
    print(f"  >> PASSED: Full answer matched all 5 concepts with tech_score={res['technical_score']}, overall={res['overall_score']}.")


def test_4_complex_analysis_partial_answer():
    """Verify partial answer receives credit ONLY for concepts covered without score inflation."""
    print("\n--- Test 4: Complex Analysis Partial Answer Evaluation ---")
    q = "How would you explain a complex analysis to a non-technical person?"
    # Only mentions avoiding jargon and simplifying, no findings, no example, no business impact
    ans = "I would avoid jargon and talk in plain English to simplify the information for them."
    res = evaluate_question(q, candidate_answer=ans, expected_concepts=get_expected_concepts(q, role="Data Analyst"))

    assert "use non-technical language and avoid jargon" in res["matched_concepts"]
    assert "simplify complex technical information" in res["matched_concepts"]
    assert "provide a relatable example" in res["missing_concepts"]
    assert "connect findings to practical or business impact" in res["missing_concepts"]
    assert "explain key findings clearly" in res["missing_concepts"]
    assert len(res["matched_concepts"]) == 2
    assert len(res["missing_concepts"]) == 3
    assert res["technical_score"] < 50.0
    print(f"  >> PASSED: Partial answer matched exactly 2/5 concepts; tech_score={res['technical_score']}.")


def test_5_complex_analysis_unrelated_negative():
    """Verify completely unrelated answer receives 0 matched concepts and 0 tech score."""
    print("\n--- Test 5: Complex Analysis Unrelated Answer Negative Test ---")
    q = "How would you explain a complex analysis to a non-technical person?"
    ans = "I really love going to the beach on weekends, eating pepperoni pizza, and swimming in the ocean."
    res = evaluate_question(q, candidate_answer=ans, expected_concepts=get_expected_concepts(q, role="Data Analyst"))

    assert len(res["matched_concepts"]) == 0, f"Expected 0 matches, got: {res['matched_concepts']}"
    assert len(res["missing_concepts"]) == 5
    assert res["technical_score"] == 0.0
    print("  >> PASSED: Unrelated answer matched 0 concepts with 0 technical score.")


def test_6_complex_analysis_unanswered():
    """Verify unanswered question receives strict 0 score and lists all 5 concepts as missing."""
    print("\n--- Test 6: Complex Analysis Unanswered Evaluation ---")
    q = "How would you explain a complex analysis to a non-technical person?"
    res = evaluate_question(q, candidate_answer="", expected_concepts=get_expected_concepts(q, role="Data Analyst"))

    assert res["technical_score"] == 0.0
    assert res["overall_score"] == 0.0
    assert res["matched_concepts"] == []
    assert len(res["missing_concepts"]) == 5
    print("  >> PASSED: Unanswered question scored 0.0 with all 5 missing concepts.")


def test_7_speech_phonetic_normalization():
    """Verify phonetic normalizations for Tableau, skills are, and projects."""
    print("\n--- Test 7: Speech Recognition Phonetic Normalization ---")
    raw1 = "And my skill serve, Python, Power BI, SQL, Excel, Diablo, etc."
    norm1 = normalize_for_matching(raw1)
    assert "my skills are" in norm1, f"Expected 'my skills are' in '{norm1}'"
    assert "tableau" in norm1, f"Expected 'tableau' in '{norm1}'"

    raw2 = "And my skill serve Python, Power BI, and Data Blue."
    norm2 = normalize_for_matching(raw2)
    assert "my skills are" in norm2
    assert "tableau" in norm2

    raw3 = "And I don't projects like multi-moderator interview evaluation system and those in this detection."
    norm3 = normalize_for_matching(raw3)
    assert "i did projects" in norm3
    assert "drowsiness detection" in norm3

    # Verify role-specific initial prompts
    p_data = get_initial_prompt("Data Analyst")
    assert "Tableau" in p_data
    assert "Power BI" in p_data
    assert "drowsiness detection" in p_data

    p_web = get_initial_prompt("Web Developer")
    assert "responsive web design" in p_web
    assert "media queries" in p_web

    p_py = get_initial_prompt("Python Developer")
    assert "MRO" in p_py
    assert "FastAPI" in p_py

    print("  >> PASSED: Phonetic normalizations and role-aware STT prompts verified.")


def test_8_grounded_feedback():
    """Verify candidate feedback does not invent communication praise on short or irrelevant answers."""
    print("\n--- Test 8: Evidence-Based Candidate Feedback ---")
    q = "What are your strengths and how can they help you in this role?"
    # Short 6-word answer without structure
    short_ans = "core strengths technical skills and communication."
    res = evaluate_question(q, candidate_answer=short_ans, expected_concepts=get_expected_concepts(q))

    # Communication was clear and structured should NOT be in strengths because words < 25
    for s in res.get("strengths", []):
        assert "Communication was clear and structured" not in s, f"Ungrounded communication praise found: {s}"

    print("  >> PASSED: Ungrounded communication praise correctly prevented for brief responses.")


def test_9_fallback_quality():
    """Verify fallback does not generate awkward phrases and logs configuration warning."""
    print("\n--- Test 9: Unknown-Question Safe Fallback Quality ---")
    unknown_q = "How does Apache Spark handle memory management and RDD lineage?"
    fallback = generate_fallback_concepts(unknown_q, role="Data Analyst")
    assert len(fallback) >= 3
    for c in fallback:
        assert "implementation" not in c.lower(), f"Awkward template in fallback: {c}"
        assert len(c.split()) >= 2
    print(f"  >> PASSED: Safe fallback generated clean concepts: {fallback}")


def test_10_mro_and_previous_fixes_regression():
    """Verify MRO (Interview #86), Responsive Design (Interview #83), and Data Profiling (#80) remain 100% functional."""
    print("\n--- Test 10: Previous Fixes Regression Integrity ---")
    # MRO
    mro_c = get_expected_concepts("What is MRO in Python?", role="Python Developer")
    assert len(mro_c) == 5
    assert "c3 linearization algorithm" in mro_c

    # Responsive Web Design
    rwd_c = get_expected_concepts("What is responsive web design and media queries?", role="Web Developer")
    assert len(rwd_c) == 6
    assert "mobile-first design" in rwd_c

    # Data Profiling
    dp_c = get_expected_concepts("What is data profiling?", role="Data Analyst")
    assert len(dp_c) == 6
    assert "examining dataset structure" in dp_c

    # JUnit
    junit_c = get_expected_concepts("What is JUnit?", role="Java Developer")
    assert len(junit_c) == 5
    assert "java unit testing framework" in junit_c

    print("  >> PASSED: MRO, Responsive Design, Data Profiling, and JUnit concepts intact.")


def test_11_historical_interview_immutability():
    """Verify historical interviews #94, #86, #83, #80, #79, and #76 are completely unmodified."""
    print("\n--- Test 11: Historical Database Immutability Audit ---")
    conn = get_connection()
    cur = conn.cursor()

    historical_records = {
        94: {"role": "Data Analyst", "score": 50.18, "status": "COMPLETED"},
        86: {"role": "Python Developer", "score": 50.18, "status": "COMPLETED"},
        83: {"role": "Web Developer", "score": 43.35, "status": "COMPLETED"},
        80: {"role": "Data Analyst", "score": 39.31, "status": "COMPLETED"},
        79: {"role": "Java Developer", "score": 24.93, "status": "COMPLETED"},
        76: {"role": "Web Developer", "score": 34.53, "status": "COMPLETED"}
    }

    for int_id, exp in historical_records.items():
        cur.execute("SELECT id, role, overall_score, status FROM Interviews WHERE id = ?", (int_id,))
        row = cur.fetchone()
        assert row is not None, f"Interview #{int_id} not found in database!"
        assert row[1] == exp["role"], f"Role mismatch for #{int_id}: expected {exp['role']}, got {row[1]}"
        assert abs(float(row[2]) - exp["score"]) < 0.01, f"Score mismatch for #{int_id}: expected {exp['score']}, got {row[2]}"
        assert row[3] == exp["status"], f"Status mismatch for #{int_id}: expected {exp['status']}, got {row[3]}"
        print(f"  Interview #{int_id}: Role={row[1]}, Score={float(row[2]):.2f}, Status={row[3]} [IMMUTABLE]")

    # Check Interview 94 Q3 enriched response
    api_94 = get_interview(94)
    q3_94 = api_94["answers"][2]
    assert q3_94["overall_answer_score"] == 0.0, "Historical Q3 score must remain 0.0"
    assert len(q3_94["expected_concepts"]) == 5, f"Expected 5 concepts in Q3 API, got {len(q3_94['expected_concepts'])}"
    assert "simplify complex technical information" in q3_94["expected_concepts"]
    print("  Interview #94: Q3 Result API payload verified with 5 expected concepts and historical 0.0 score.")

    cur.close()
    conn.close()
    print("  >> PASSED: All 6 historical interview records and scores are 100% immutable.")


def test_12_fresh_data_analyst_e2e_interview():
    """Run a fresh 3-question Data Analyst interview, persist to SQL Server, and verify via get_interview API."""
    print("\n--- Test 12: Fresh Data Analyst E2E Interview & Persistence Verification ---")
    q1_text = "Tell me about yourself."
    q2_text = "What are your strengths and how can they help you in this role?"
    q3_text = "How would you explain a complex analysis to a non-technical person?"

    q1_ans = (
        "Hi, my name is Priya. I completed my B.Tech degree at State Technical University. "
        "I have worked on data analytics projects involving Python, SQL, and Power BI dashboards."
    )
    q2_ans = (
        "My core strengths are analytical problem-solving and proactive communication. "
        "For example, in my previous internship, I identified revenue leakage by auditing SQL billing logs."
    )
    q3_ans = (
        "To explain complex analysis to a non-technical person, I simplify complex technical information "
        "and avoid jargon by speaking in plain English. I highlight key findings clearly with visual charts, "
        "provide a relatable real-world example, and always connect the insights to business impact and actionable next steps."
    )

    session_payload = [
        {
            "question_number": 1,
            "question": q1_text,
            "candidate_answer": q1_ans,
            "expected_concepts": get_expected_concepts(q1_text, role="Data Analyst"),
            "category": "Introduction",
            "is_answered": True,
            "words_spoken": len(q1_ans.split()),
            "start_ms": 0,
            "end_ms": 14000
        },
        {
            "question_number": 2,
            "question": q2_text,
            "candidate_answer": q2_ans,
            "expected_concepts": get_expected_concepts(q2_text, role="Data Analyst"),
            "category": "HR",
            "is_answered": True,
            "words_spoken": len(q2_ans.split()),
            "start_ms": 15000,
            "end_ms": 30000
        },
        {
            "question_number": 3,
            "question": q3_text,
            "candidate_answer": q3_ans,
            "expected_concepts": get_expected_concepts(q3_text, role="Data Analyst"),
            "category": "Technical",
            "is_answered": True,
            "words_spoken": len(q3_ans.split()),
            "start_ms": 31000,
            "end_ms": 52000
        }
    ]

    eval_res = evaluate_interview(session_payload)
    assert eval_res["total_questions"] == 3
    assert eval_res["answered_questions"] == 3
    assert eval_res["unanswered_questions"] == 0
    assert eval_res["overall_score"] >= 75.0

    q3_eval = eval_res["questions"][2]
    assert len(q3_eval["matched_concepts"]) == 5
    assert len(q3_eval["missing_concepts"]) == 0
    assert q3_eval["technical_score"] == 100.0

    # Persist fresh interview to SQL Server
    q_data_list = [
        {"question_number": 1, "question_text": q1_text, "relative_start": 0.0, "relative_end": 14.0},
        {"question_number": 2, "question_text": q2_text, "relative_start": 15.0, "relative_end": 30.0},
        {"question_number": 3, "question_text": q3_text, "relative_start": 31.0, "relative_end": 52.0}
    ]

    fresh_id = save_interview_record(
        role="Data Analyst",
        total_questions=3,
        recording_path="uploads/Data_Analyst_fresh_system_wide_test.webm",
        transcript=f"{q1_ans} {q2_ans} {q3_ans}",
        tab_switch_count=0,
        terminated_reason="",
        evaluation=eval_res,
        question_data_list=q_data_list,
        language="en",
        filename="Data_Analyst_fresh_system_wide_test.webm",
        user_id=14
    )
    print(f"  Persisted fresh Data Analyst interview to DB with ID: {fresh_id}")

    # Fetch and verify via get_interview API
    api_data = get_interview(fresh_id)
    assert api_data["status"] == "success"
    assert api_data["interview"]["role"] == "Data Analyst"
    assert len(api_data["answers"]) == 3

    ans3_api = api_data["answers"][2]
    assert ans3_api["question_text"] == q3_text
    assert len(ans3_api["expected_concepts"]) == 5
    assert ans3_api["technical_score"] == 100.0
    matched_3 = json.loads(ans3_api["matched_concepts"]) if isinstance(ans3_api["matched_concepts"], str) else ans3_api["matched_concepts"]
    assert len(matched_3) == 5

    print(f"  >> PASSED: Fresh Data Analyst interview (ID #{fresh_id}) evaluated and persisted with 100% Q3 concept match.")


def run_all_tests():
    print("=" * 70)
    print("STARTING SYSTEM-WIDE REGRESSION & AUDIT TEST SUITE")
    print("=" * 70)

    tests = [
        test_1_all_roles_question_coverage,
        test_2_complex_analysis_expected_concepts,
        test_3_complex_analysis_full_answer,
        test_4_complex_analysis_partial_answer,
        test_5_complex_analysis_unrelated_negative,
        test_6_complex_analysis_unanswered,
        test_7_speech_phonetic_normalization,
        test_8_grounded_feedback,
        test_9_fallback_quality,
        test_10_mro_and_previous_fixes_regression,
        test_11_historical_interview_immutability,
        test_12_fresh_data_analyst_e2e_interview
    ]

    passed = 0
    failed = 0

    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"  >> FAILED: {t.__name__} - {e}")
            failed += 1
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 70)
    print(f"TEST RESULTS: {passed} PASSED, {failed} FAILED (TOTAL {len(tests)})")
    print("=" * 70)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
