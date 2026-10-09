import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from evaluation import evaluate_question, evaluate_interview, is_concept_matched
from question_bank import get_expected_concepts

def test_regression():
    print("=" * 60)
    print("RUNNING REGRESSION TESTS")
    print("=" * 60)

    # 1. Final-year student introduction with imperfect transcription: education must be matched
    q1 = "Tell me about yourself."
    exp1 = get_expected_concepts(q1)
    ans1 = "Hi, my name is Navin Kumar, both parties currently pursuing meeting final year in PPSA, one university."
    r1 = evaluate_question(q1, candidate_answer=ans1, expected_concepts=exp1)
    print("\n[Test 1] Final-year student introduction with imperfect transcription:")
    print("Answer:", ans1)
    print("Matched:", r1["matched_concepts"])
    print("Missing:", r1["missing_concepts"])
    print("Tech Score:", r1["technical_score"], "Relevance:", r1["relevance_score"], "Overall:", r1["overall_score"])
    assert "education" in r1["matched_concepts"], "Test 1 Failed: education was not matched"
    print(">> Test 1 PASSED: education matched")

    # Also test variants of education statements:
    edu_variants = [
        "I am pursuing B.Tech in Computer Science.",
        "I am in my final year of engineering.",
        "Currently studying at university.",
        "Currently persuing btech in final ear.",
        "I am in final air of college."
    ]
    for ev in edu_variants:
        res = is_concept_matched("education", ev)
        print(f"  Edu variant '{ev}' -> {res}")
        assert res, f"Failed for education variant: {ev}"
    print(">> Education variants all PASSED")

    # 2. Introduction that mentions Python, SQL, and Power BI: technical skills must be matched
    ans2 = "Hello, my name is Priya. My technical skills include Python, SQL, and Power BI."
    r2 = evaluate_question(q1, candidate_answer=ans2, expected_concepts=exp1)
    print("\n[Test 2] Introduction mentioning Python, SQL, and Power BI:")
    print("Matched:", r2["matched_concepts"])
    assert "technical skills" in r2["matched_concepts"], "Test 2 Failed: technical skills was not matched"
    print(">> Test 2 PASSED: technical skills matched")

    # 3. Introduction with no mention of projects: projects must remain missing
    print("\n[Test 3] Introduction with no mention of projects:")
    print("In Test 1 answer, matched:", r1["matched_concepts"])
    assert "projects" not in r1["matched_concepts"], "Test 3 Failed: projects should not be matched"
    assert "projects" in r1["missing_concepts"], "Test 3 Failed: projects must be in missing_concepts"
    print(">> Test 3 PASSED: projects remains missing")

    # 4. Answer mentioning internships: relevant experience should be matched
    ans4 = "During my summer break, I completed a data analyst internship at an analytics startup."
    r4 = evaluate_question(q1, candidate_answer=ans4, expected_concepts=exp1)
    print("\n[Test 4] Answer mentioning internships:")
    print("Matched:", r4["matched_concepts"])
    assert "relevant experience" in r4["matched_concepts"], "Test 4 Failed: relevant experience was not matched"
    print(">> Test 4 PASSED: relevant experience matched")

    # 5. Answer that mentions no career goals: career goals must remain missing
    print("\n[Test 5] Answer with no career goals:")
    assert "career goals" not in r1["matched_concepts"], "Test 5 Failed: career goals should not be matched"
    assert "career goals" in r1["missing_concepts"], "Test 5 Failed: career goals must be in missing_concepts"
    print(">> Test 5 PASSED: career goals remains missing")

    # 6. Existing Q2 strengths answer: do not fabricate communication, problem-solving, or practical-example evidence
    q2 = "What are your strengths and how can they help you in this role?"
    exp2 = get_expected_concepts(q2)
    ans6 = "All my core stands are core stand technical skills, all to the work."
    r6 = evaluate_question(q2, candidate_answer=ans6, expected_concepts=exp2)
    print("\n[Test 6] Existing Q2 strengths answer:")
    print("Matched:", r6["matched_concepts"])
    print("Missing:", r6["missing_concepts"])
    print("Scores - Tech:", r6["technical_score"], "Rel:", r6["relevance_score"], 
          "Comm:", r6["communication_score"], "Prob:", r6["problem_solving_score"], "Overall:", r6["overall_score"])
    assert "communication" not in r6["matched_concepts"], "Test 6 Failed: communication must not be matched"
    assert "problem solving" not in r6["matched_concepts"], "Test 6 Failed: problem solving must not be matched"
    assert "practical example" not in r6["matched_concepts"], "Test 6 Failed: practical example must not be matched"
    print(">> Test 6 PASSED: communication, problem solving, practical example are not fabricated")

    # 7. Empty VLOOKUP answer: every score remains zero
    q3 = "What is VLOOKUP?"
    exp3 = get_expected_concepts(q3)
    ans7 = ""
    r7 = evaluate_question(q3, candidate_answer=ans7, expected_concepts=exp3)
    print("\n[Test 7] Empty VLOOKUP answer:")
    for key, val in r7.items():
        if "score" in key:
            print(f"  {key}: {val}")
            assert val == 0.0, f"Test 7 Failed: {key} is {val}, expected 0.0"
    assert r7["matched_concepts"] == [], "Test 7 Failed: matched_concepts should be empty"
    print(">> Test 7 PASSED: all scores are 0.0")

    # Test empty answer in evaluate_interview
    interview_payload = [
        {"question_number": 1, "question": q1, "candidate_answer": ans1, "expected_concepts": exp1},
        {"question_number": 2, "question": q2, "candidate_answer": ans6, "expected_concepts": exp2},
        {"question_number": 3, "question": q3, "candidate_answer": "", "expected_concepts": exp3}
    ]
    interv_res = evaluate_interview(interview_payload)
    print("\nInterview Evaluation Summary:")
    print("Total:", interv_res["total_questions"], "Answered:", interv_res["answered_questions"], "Unanswered:", interv_res["unanswered_questions"])
    print("Overall Score:", interv_res["overall_score"])
    q3_res = interv_res["questions"][2]
    assert q3_res["is_answered"] is False, "Q3 must have is_answered=False"
    assert q3_res["status"] == "not_answered", "Q3 must have status=not_answered"
    assert q3_res["overall_score"] == 0.0, "Q3 overall_score must be 0"

    # 8. Unrelated answer: must not receive an unjustifiably high technical score
    ans8 = "I really love eating pizza and watching action movies every Sunday afternoon."
    r8 = evaluate_question(q3, candidate_answer=ans8, expected_concepts=exp3)
    print("\n[Test 8] Unrelated answer:")
    print("Answer:", ans8)
    print("Tech Score:", r8["technical_score"], "Relevance:", r8["relevance_score"], "Overall:", r8["overall_score"])
    print("Matched:", r8["matched_concepts"])
    assert r8["technical_score"] <= 10.0, f"Test 8 Failed: technical score {r8['technical_score']} is too high"
    assert r8["relevance_score"] <= 15.0, f"Test 8 Failed: relevance score {r8['relevance_score']} is too high"
    assert len(r8["matched_concepts"]) == 0, f"Test 8 Failed: matched concepts should be empty"
    print(">> Test 8 PASSED: unrelated answer has low scores and 0 matched concepts")

    # 9. High-quality comprehensive answer: should receive high score (> 75)
    ans9 = ("Normalization in SQL is the process of organizing database tables to reduce data redundancy and eliminate "
            "duplicate data, which ensures data integrity. It splits large tables into smaller related tables using normal forms.")
    q_norm = "What is normalization in SQL?"
    exp_norm = get_expected_concepts(q_norm)
    r9 = evaluate_question(q_norm, candidate_answer=ans9, expected_concepts=exp_norm)
    print("\n[Test 9] High-quality comprehensive answer:")
    print("Matched:", r9["matched_concepts"])
    print("Scores - Tech:", r9["technical_score"], "Rel:", r9["relevance_score"], "Overall:", r9["overall_score"])
    assert len(r9["matched_concepts"]) >= 4, f"Test 9 Failed: expected at least 4 concepts matched, got {len(r9['matched_concepts'])}"
    assert r9["technical_score"] >= 70.0, f"Test 9 Failed: technical score {r9['technical_score']} should be >= 70"
    assert r9["overall_score"] >= 70.0, f"Test 9 Failed: overall score {r9['overall_score']} should be >= 70"
    print(">> Test 9 PASSED: high quality answer receives appropriately high scores")

    # 10. VLOOKUP correctly answered
    ans10 = ("VLOOKUP stands for vertical lookup in Excel. It searches for a lookup value in the first column of a table array, "
             "and returns a value from the specified column index number using exact or approximate match.")
    r10 = evaluate_question(q3, candidate_answer=ans10, expected_concepts=exp3)
    print("\n[Test 10] Correct VLOOKUP explanation:")
    print("Matched:", r10["matched_concepts"])
    print("Scores - Tech:", r10["technical_score"], "Rel:", r10["relevance_score"], "Overall:", r10["overall_score"])
    assert "vertical lookup" in r10["matched_concepts"] or "lookup value" in r10["matched_concepts"], "Test 10 Failed: VLOOKUP concepts not matched"
    assert r10["technical_score"] >= 70.0, f"Test 10 Failed: technical score {r10['technical_score']} should be >= 70"
    print(">> Test 10 PASSED: VLOOKUP concepts matched correctly")

    # 11. Latest recorded evaluation data (Python Developer interview run - Row 53)
    print("\n[Test 11] Latest recorded evaluation data (Python Developer interview run):")
    q1_text = "Tell me about yourself."
    exp1_concepts = get_expected_concepts(q1_text)
    ans11_1 = "Hi, my name is Naveen Kumar, I am currently pursuing BTEC, finally here in PPSA on University and I am passionate about data and I have learned skills like Excel, Power BI, SQL and Python and I will do data cleaning and prepositing etc."
    r11_1 = evaluate_question(q1_text, candidate_answer=ans11_1, expected_concepts=exp1_concepts)
    print("  Q1 Matched:", r11_1["matched_concepts"])
    print("  Q1 Scores - Tech:", r11_1["technical_score"], "Rel:", r11_1["relevance_score"], "Overall:", r11_1["overall_score"])
    assert r11_1["technical_score"] == 40.0, f"Q1 tech score expected 40.0, got {r11_1['technical_score']}"
    assert abs(r11_1["overall_score"] - 45.11) < 0.1, f"Q1 overall score expected ~45.11, got {r11_1['overall_score']}"
    assert set(r11_1["matched_concepts"]) == {"education", "technical skills"}
    assert set(r11_1["missing_concepts"]) == {"relevant experience", "projects", "career goals"}

    q2_text = "What are your strengths and how can they help you in this role?"
    exp2_concepts = get_expected_concepts(q2_text)
    ans11_2 = "on my core strands and how can I help in the storage technique by using the technical skills as well as core stance."
    r11_2 = evaluate_question(q2_text, candidate_answer=ans11_2, expected_concepts=exp2_concepts)
    print("  Q2 Matched:", r11_2["matched_concepts"])
    print("  Q2 Scores - Tech:", r11_2["technical_score"], "Rel:", r11_2["relevance_score"], "Overall:", r11_2["overall_score"])
    assert r11_2["technical_score"] == 20.31, f"Q2 tech score expected 20.31, got {r11_2['technical_score']}"
    assert r11_2["relevance_score"] == 21.25, f"Q2 relevance score expected 21.25, got {r11_2['relevance_score']}"
    assert abs(r11_2["overall_score"] - 26.86) < 0.1, f"Q2 overall score expected ~26.86, got {r11_2['overall_score']}"
    assert r11_2["matched_concepts"] == ["core strengths"]
    assert "communication" in r11_2["missing_concepts"]
    assert "practical example" in r11_2["missing_concepts"]

    q3_text = "What is Python and what are its main features?"
    exp3_concepts = get_expected_concepts(q3_text)
    r11_3 = evaluate_question(q3_text, candidate_answer="", expected_concepts=exp3_concepts)
    assert r11_3["technical_score"] == 0.0
    assert r11_3["overall_score"] == 0.0

    # Test full interview evaluation for this 3-question session
    session_payload = [
        {"question_number": 1, "question": q1_text, "candidate_answer": ans11_1, "expected_concepts": exp1_concepts},
        {"question_number": 2, "question": q2_text, "candidate_answer": ans11_2, "expected_concepts": exp2_concepts},
        {"question_number": 3, "question": q3_text, "candidate_answer": "", "expected_concepts": exp3_concepts}
    ]
    interv_session = evaluate_interview(session_payload)
    print("  Interview Averages - Tech:", interv_session["technical_score"], "Rel:", interv_session["relevance_score"], "Overall:", interv_session["overall_score"])
    assert interv_session["total_questions"] == 3
    assert interv_session["answered_questions"] == 2
    assert interv_session["unanswered_questions"] == 1
    assert interv_session["technical_score"] == 30.16, f"Expected 30.16, got {interv_session['technical_score']}"
    assert interv_session["relevance_score"] == 30.62, f"Expected 30.62, got {interv_session['relevance_score']}"
    assert interv_session["overall_score"] == 34.85, f"Expected 34.85, got {interv_session['overall_score']}"
    print(">> Test 11 PASSED: Latest recorded interview evaluation faithfully reproduced and verified")

    # 12. Edge Case: Punctuation, noise, and whitespace-only answers
    print("\n[Test 12] Edge Cases: Non-substantive answers (punctuation, whitespace, noise):")
    noise_answers = ["...", ",,,", "---", "  \n\t  ", "!@#$%", "   ...   "]
    for na in noise_answers:
        res = evaluate_question(q3_text, candidate_answer=na, expected_concepts=exp3_concepts)
        assert res["technical_score"] == 0.0, f"Failed for '{na}': tech score {res['technical_score']}"
        assert res["overall_score"] == 0.0, f"Failed for '{na}': overall score {res['overall_score']}"
        assert res["evaluation_source"] == "empty_answer"

    # In interview context, noise answers must have is_answered=False and be excluded from average
    noise_payload = [
        {"question_number": 1, "question": q1_text, "candidate_answer": ans11_1, "expected_concepts": exp1_concepts},
        {"question_number": 2, "question": q2_text, "candidate_answer": "...", "expected_concepts": exp2_concepts}
    ]
    interv_noise = evaluate_interview(noise_payload)
    assert interv_noise["answered_questions"] == 1, f"Expected 1 answered, got {interv_noise['answered_questions']}"
    assert interv_noise["unanswered_questions"] == 1
    assert interv_noise["overall_score"] == r11_1["overall_score"], "Noise answer must be excluded from average"
    print(">> Test 12 PASSED: Non-substantive answers properly recognized as empty and excluded from average")

    # 13. Edge Case: All questions unanswered in interview
    print("\n[Test 13] Edge Case: Entire interview unanswered:")
    all_empty_payload = [
        {"question_number": 1, "question": q1_text, "candidate_answer": "", "expected_concepts": exp1_concepts},
        {"question_number": 2, "question": q2_text, "candidate_answer": "   ", "expected_concepts": exp2_concepts}
    ]
    interv_all_empty = evaluate_interview(all_empty_payload)
    assert interv_all_empty["answered_questions"] == 0
    assert interv_all_empty["unanswered_questions"] == 2
    assert interv_all_empty["overall_score"] == 0.0
    assert interv_all_empty["technical_score"] == 0.0
    print(">> Test 13 PASSED: All-unanswered interview returns 0.0 scores with no division errors")

    # 14. Verification of Configured Weights and Score Bounds
    print("\n[Test 14] Verification of Configured Weights & Clamping Bounds:")
    from evaluation import WEIGHTS, clamp_score, calculate_overall
    weight_sum = round(sum(WEIGHTS.values()), 4)
    assert weight_sum == 1.0, f"Weights sum must be 1.0, got {weight_sum}"
    expected_weights = {
        "technical_score": 0.35,
        "relevance_score": 0.20,
        "concept_score": 0.15,
        "completeness_score": 0.10,
        "communication_score": 0.10,
        "confidence_score": 0.05,
        "problem_solving_score": 0.05
    }
    for k, v in expected_weights.items():
        assert WEIGHTS.get(k) == v, f"Weight for {k} expected {v}, got {WEIGHTS.get(k)}"

    # Test clamping bounds
    assert clamp_score(-10) == 0.0
    assert clamp_score(150) == 100.0
    assert clamp_score("invalid") == 0.0
    assert clamp_score(9.375) == 9.38

    # Test calculate_overall bounds
    assert calculate_overall(100, 100, 100, 100, 100, 100, 100) == 100.0
    assert calculate_overall(0, 0, 0, 0, 0, 0, 0) == 0.0
    assert calculate_overall(-50, -50, -50, -50, -50, -50, -50) == 0.0
    assert calculate_overall(200, 200, 200, 200, 200, 200, 200) == 100.0
    print(">> Test 14 PASSED: Weights and clamping bounds verified")

    print("\n" + "=" * 60)
    print("ALL REGRESSION TESTS COMPLETED SUCCESSFULLY")
    print("=" * 60)

if __name__ == "__main__":
    test_regression()


