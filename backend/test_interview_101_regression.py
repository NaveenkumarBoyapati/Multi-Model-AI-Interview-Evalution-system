"""
Comprehensive Regression & Verification Test Suite for Interview #101 Audit & Fixes.

Covers:
1. Historical Database Immutability for Interview #101, #94, #86, #83, #80, #79, #76.
2. Speech-to-Text Phonetic Normalization ('pursuing B.Tech finally', 'co-strengths', 'being motive').
3. Role-Aware Transcription Prompts for Technical Roles.
4. Concept Matching for Candidate's Q1 and Q2 Spoken Answers (with zero false positives).
5. Documented Scoring Formula, Category Weights, Rounding, and Aggregation (Q1=63, Q2=41, Overall=50).
6. Evidence-Based Strengths & Improvements Feedback Generation.
7. Interview Lifecycle: 2-Question Early Finish Support vs 3-Question Interview Support.
8. API Retrieval and Dynamic Enrichment for Interview #101.
9. Fresh End-to-End Interview Execution & Database Persistence.
"""

import sys
import os
import json
import pyodbc

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_connection
from question_bank import get_expected_concepts
from transcription import get_initial_prompt
from evaluation import (
    evaluate_question,
    evaluate_interview,
    normalize_for_matching,
    is_concept_matched,
    calculate_overall,
    WEIGHTS
)
from main import get_interview, save_interview_record


def test_1_historical_interview_101_immutability():
    """Verify historical interview #101 and prior interviews remain 100% immutable."""
    print("\n--- Test 1: Historical Database Immutability ---")
    conn = get_connection()
    cur = conn.cursor()

    # Interview #101
    cur.execute("SELECT id, role, overall_score, total_questions, status FROM Interviews WHERE id = 101")
    row101 = cur.fetchone()
    assert row101 is not None, "Interview #101 missing from database!"
    assert row101[1] == "Data Analyst"
    assert abs(float(row101[2]) - 50.36) < 0.05, f"Interview #101 overall score changed: {row101[2]}"
    assert row101[3] == 2, f"Interview #101 total_questions changed: {row101[3]}"
    assert row101[4] == "COMPLETED"

    # Prior interviews
    priors = {
        94: 50.18,
        86: 50.18,
        83: 43.35,
        80: 39.31,
        79: 24.93,
        76: 34.53
    }
    for i_id, exp_score in priors.items():
        cur.execute("SELECT overall_score FROM Interviews WHERE id = ?", (i_id,))
        r = cur.fetchone()
        assert r is not None, f"Interview #{i_id} not found!"
        assert abs(float(r[0]) - exp_score) < 0.05, f"Interview #{i_id} score changed: {r[0]} vs {exp_score}"

    cur.close()
    conn.close()
    print("  >> PASSED: Historical Interview #101 and all prior interviews are 100% immutable.")


def test_2_speech_recognition_phonetic_normalizations():
    """Verify phonetic normalizations for #101 acoustic variations."""
    print("\n--- Test 2: Speech-to-Text Phonetic Normalization ---")
    
    # 1. B.Tech finally in -> final year
    raw_edu = "I am currently pursuing B.Tech finally in P.P. Savani University"
    norm_edu = normalize_for_matching(raw_edu)
    assert "final year" in norm_edu, f"Failed to normalize 'finally in' to 'final year': {norm_edu}"
    assert is_concept_matched("education", raw_edu)

    # 2. co- strengths -> core strengths
    raw_str = "And my co- strengths and technical skills are communicating."
    norm_str = normalize_for_matching(raw_str)
    assert "core strengths" in norm_str, f"Failed to normalize 'co- strengths': {norm_str}"
    assert is_concept_matched("core strengths", raw_str)

    # 3. being motive -> being motivated
    raw_motive = "communication, strength, being motive, helping others."
    norm_motive = normalize_for_matching(raw_motive)
    assert "being motivated" in norm_motive, f"Failed to normalize 'being motive': {norm_motive}"
    assert is_concept_matched("core strengths", raw_motive)

    print("  >> PASSED: All suspicious STT phrases normalized accurately without fabricating text.")


def test_3_role_aware_transcription_prompts():
    """Verify role-aware prompts include final year and behavioral vocabulary."""
    print("\n--- Test 3: Role-Aware Faster-Whisper Prompts ---")
    roles = ["Data Analyst", "Web Developer", "Java Developer", "Python Developer"]
    for role in roles:
        prompt = get_initial_prompt(role)
        assert "B.Tech final year" in prompt, f"Missing final year in prompt for {role}"
        assert "communication" in prompt.lower()
        assert "strengths" in prompt.lower()
    print("  >> PASSED: All 4 role prompts provide domain vocabulary for degrees and core strengths.")


def test_4_concept_matching_and_relevance():
    """Verify concept matching for Interview #101 answers with zero false positives."""
    print("\n--- Test 4: Concept Matching for Interview #101 Answers ---")
    
    # Q1 Answer
    q1_text = "Tell me about yourself."
    q1_ans = (
        "Hi, my name is Naveen Kumar Boipati. I am currently pursuing B .Tech finally in P .P. Savani University "
        "and I done several projects like face recognition, multimodal interview, evaluation, drowsiness detection, etcetera. "
        "And I have skills like Power BI, Excel, SQL, etcetera."
    )
    res_q1 = evaluate_question(q1_text, candidate_answer=q1_ans, expected_concepts=get_expected_concepts(q1_text))
    assert "education" in res_q1["matched_concepts"]
    assert "technical skills" in res_q1["matched_concepts"]
    assert "projects" in res_q1["matched_concepts"]
    assert "relevant experience" in res_q1["missing_concepts"]
    assert "career goals" in res_q1["missing_concepts"]
    assert res_q1["problem_solving_score"] is None, "Self-intro should have None for problem solving unless demonstrated"

    # Q2 Answer
    q2_text = "What are your strengths and how can they help you in this role?"
    q2_ans = "And my co - strengths and technical skills are communicating. communication, strength, being motive, helping others."
    res_q2 = evaluate_question(q2_text, candidate_answer=q2_ans, expected_concepts=get_expected_concepts(q2_text))
    assert "core strengths" in res_q2["matched_concepts"]
    assert "communication" in res_q2["matched_concepts"]
    assert "problem-solving" in res_q2["missing_concepts"]
    assert "practical example" in res_q2["missing_concepts"]
    assert "role contribution" in res_q2["missing_concepts"]
    assert res_q2["problem_solving_score"] == 0.0, "Incomplete strengths with no problem solving must be 0.0"

    print("  >> PASSED: Matched and missing concepts perfectly align with spoken evidence.")


def test_5_scoring_formula_and_aggregation():
    """Verify exact mathematical aggregation for Interview #101 (Q1=63, Q2=41, Overall=50.36 -> 50)."""
    print("\n--- Test 5: Scoring Formula & Aggregation Verification ---")
    
    # Weights verification
    assert round(sum(WEIGHTS.values()), 4) == 1.0

    # Q1 Calculation: 6 categories active, problem_solving is None
    q1_scores = {
        "technical_score": 60.0,
        "relevance_score": 60.0,
        "concept_score": 60.0,
        "completeness_score": 60.0,
        "communication_score": 85.0,
        "confidence_score": 67.0,
        "problem_solving_score": None
    }
    q1_overall = calculate_overall(**q1_scores)
    assert q1_overall == 63.0, f"Expected Q1=63.0, got {q1_overall}"

    # Q2 Calculation: all 7 categories active (problem solving = 0.0)
    q2_scores = {
        "technical_score": 36.25,
        "relevance_score": 36.25,
        "concept_score": 36.25,
        "completeness_score": 40.0,
        "communication_score": 85.0,
        "confidence_score": 60.0,
        "problem_solving_score": 0.0
    }
    q2_overall = calculate_overall(**q2_scores)
    assert q2_overall == 40.88, f"Expected Q2=40.88, got {q2_overall}"

    # Aggregated interview calculation:
    avg_tech = round((60.0 + 36.25) / 2, 2)
    avg_rel = round((60.0 + 36.25) / 2, 2)
    avg_concept = round((60.0 + 36.25) / 2, 2)
    avg_comp = round((60.0 + 40.0) / 2, 2)
    avg_comm = round((85.0 + 85.0) / 2, 2)
    avg_conf = round((67.0 + 60.0) / 2, 2)
    avg_prob = 0.0 # From Q2

    int_overall = calculate_overall(avg_tech, avg_rel, avg_concept, avg_comp, avg_comm, avg_conf, avg_prob)
    assert int_overall == 50.36, f"Expected aggregated interview overall=50.36, got {int_overall}"
    assert round(int_overall) == 50, f"Expected UI rounded score=50, got {round(int_overall)}"

    print(f"  >> PASSED: Documented formula confirmed (Q1={q1_overall}, Q2={q2_overall}, Interview Overall={int_overall} -> 50).")


def test_6_evidence_based_candidate_feedback():
    """Verify feedback does not claim structured communication when disfluency or repetition is present."""
    print("\n--- Test 6: Evidence-Based Candidate Feedback Generation ---")
    
    # Q1 with repeated 'etcetera' and grammar issues
    q1_text = "Tell me about yourself."
    q1_ans = (
        "Hi, my name is Naveen Kumar Boipati. I am currently pursuing B .Tech finally in P .P. Savani University "
        "and I done several projects like face recognition, multimodal interview, evaluation, drowsiness detection, etcetera. "
        "And I have skills like Power BI, Excel, SQL, etcetera."
    )
    res_q1 = evaluate_question(q1_text, candidate_answer=q1_ans, expected_concepts=get_expected_concepts(q1_text))
    # Should NOT have 'Communication was clear and structured' because of repetition of etcetera
    assert "Communication was clear and structured." not in res_q1["strengths"], (
        f"Ungrounded structured praise awarded: {res_q1['strengths']}"
    )

    # Clean, well-structured answer SHOULD receive the praise
    structured_ans = (
        "Good morning. My name is Alex and I recently completed my Computer Science degree at State University. "
        "During my academic career, I developed several full-stack analytics applications using Python, SQL, and Power BI. "
        "I am eager to contribute my technical foundation to data analysis and business intelligence projects."
    )
    res_clean = evaluate_question(q1_text, candidate_answer=structured_ans, expected_concepts=get_expected_concepts(q1_text))
    assert "Communication was clear and structured." in res_clean["strengths"], (
        f"Expected structured praise for clean answer: {res_clean['strengths']}"
    )

    print("  >> PASSED: Structured communication praise accurately differentiates clean structured speech from disfluent speech.")


def test_7_question_lifecycle_and_api_retrieval():
    """Verify 2-question interview lifecycle (Interview #101) retrieved correctly via API."""
    print("\n--- Test 7: 2-Question Interview API Retrieval ---")
    data = get_interview(101)
    assert data["status"] == "success"
    assert data["interview"]["total_questions"] == 2
    assert len(data["answers"]) == 2
    
    q1 = data["answers"][0]
    assert q1["question_number"] == 1
    assert q1["overall_answer_score"] == 63.0
    assert len(q1["expected_concepts"]) == 5

    q2 = data["answers"][1]
    assert q2["question_number"] == 2
    assert q2["overall_answer_score"] == 40.88
    assert len(q2["expected_concepts"]) == 5

    print("  >> PASSED: get_interview(101) accurately returns 2 questions without phantom 3rd question.")


def test_8_fresh_2_question_e2e_interview():
    """Verify fresh 2-question interview (early finish) correctly evaluates and persists."""
    print("\n--- Test 8: Fresh 2-Question E2E Interview Persistence ---")
    session = [
        {
            "question_number": 1,
            "question": "Tell me about yourself.",
            "candidate_answer": "Hi, my name is Sara. I graduated with a degree in Statistics. I have worked on data analysis using Python and SQL.",
            "expected_concepts": get_expected_concepts("Tell me about yourself.", role="Data Analyst"),
            "category": "Introduction",
            "relative_start": 0.0,
            "relative_end": 18.0
        },
        {
            "question_number": 2,
            "question": "What are your strengths and how can they help you in this role?",
            "candidate_answer": "My primary strengths are proactive communication, teamwork, and analytical problem-solving with data.",
            "expected_concepts": get_expected_concepts("What are your strengths and how can they help you in this role?", role="Data Analyst"),
            "category": "HR",
            "relative_start": 18.0,
            "relative_end": 35.0
        }
    ]
    eval_res = evaluate_interview(session)
    assert eval_res["total_questions"] == 2
    assert eval_res["answered_questions"] == 2
    assert eval_res["unanswered_questions"] == 0

    new_id = save_interview_record(
        role="Data Analyst",
        total_questions=2,
        recording_path="uploads/test_2q_sample.webm",
        transcript="Test 2 question transcript",
        tab_switch_count=0,
        terminated_reason="",
        evaluation=eval_res,
        question_data_list=session,
        language="en",
        filename="test_2q_sample.webm"
    )

    api_res = get_interview(new_id)
    assert api_res["interview"]["total_questions"] == 2
    assert len(api_res["answers"]) == 2
    print(f"  >> PASSED: Fresh 2-question interview evaluated and saved with ID={new_id}.")


def run_all():
    tests = [
        test_1_historical_interview_101_immutability,
        test_2_speech_recognition_phonetic_normalizations,
        test_3_role_aware_transcription_prompts,
        test_4_concept_matching_and_relevance,
        test_5_scoring_formula_and_aggregation,
        test_6_evidence_based_candidate_feedback,
        test_7_question_lifecycle_and_api_retrieval,
        test_8_fresh_2_question_e2e_interview
    ]
    passed = 0
    failed = 0
    print("=" * 70)
    print("STARTING INTERVIEW #101 AUDIT & VERIFICATION TEST SUITE")
    print("=" * 70)
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"  >> FAILED: {t.__name__} - {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    print("\n" + "=" * 70)
    print(f"TEST RESULTS: {passed} PASSED, {failed} FAILED (TOTAL {len(tests)})")
    print("=" * 70)
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_all()
