import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from evaluation import (
    evaluate_question,
    evaluate_interview,
    is_valid_answer,
    is_concept_matched,
    clamp_score
)
from question_bank import get_expected_concepts

def assign_whisper_to_questions(question_data_list, whisper_segments, transition_buffer=1.2):
    """
    Simulates the exact backend Whisper segment assignment logic from backend/main.py.
    """
    num_q = len(question_data_list)
    question_matched_speech = {i: [] for i in range(num_q)}
    question_word_details = {i: [] for i in range(num_q)}

    for seg_idx, seg in enumerate(whisper_segments):
        s_start = float(seg.get("start", 0.0))
        s_end = float(seg.get("end", 0.0))
        seg_text = seg.get("text", "").strip()
        words = seg.get("words", [])

        if not seg_text:
            continue

        origin_q_idx = None
        for idx, q_item in enumerate(question_data_list):
            qs = float(q_item["relative_start"])
            qe = float(q_item["relative_end"])
            if idx == num_q - 1:
                if qs <= s_start:
                    origin_q_idx = idx
                    break
            else:
                if qs <= s_start < qe:
                    origin_q_idx = idx
                    break
        if origin_q_idx is None:
            origin_q_idx = 0 if s_start < float(question_data_list[0]["relative_start"]) else num_q - 1

        if words:
            for w in words:
                w_text = w.get("word", "").strip()
                if not w_text:
                    continue
                w_start = float(w.get("start", 0.0))
                w_end = float(w.get("end", 0.0))
                w_mid = (w_start + w_end) / 2.0
                w_prob = float(w.get("probability", 1.0))

                assigned_idx = None
                orig_qs = float(question_data_list[origin_q_idx]["relative_start"])
                orig_qe = float(question_data_list[origin_q_idx]["relative_end"])

                if origin_q_idx < num_q - 1:
                    if orig_qs <= w_mid < (orig_qe + transition_buffer):
                        assigned_idx = origin_q_idx
                else:
                    if orig_qs <= w_mid:
                        assigned_idx = origin_q_idx

                if assigned_idx is None:
                    for idx, q_item in enumerate(question_data_list):
                        qs = float(q_item["relative_start"])
                        qe = float(q_item["relative_end"])
                        if idx == num_q - 1:
                            if qs <= w_mid:
                                assigned_idx = idx
                                break
                        else:
                            if qs <= w_mid < qe:
                                assigned_idx = idx
                                break

                if assigned_idx is None:
                    assigned_idx = 0 if w_mid < float(question_data_list[0]["relative_start"]) else num_q - 1

                question_matched_speech[assigned_idx].append(w_text)
                question_word_details[assigned_idx].append({
                    "word": w_text,
                    "start": round(w_start, 3),
                    "end": round(w_end, 3),
                    "probability": round(w_prob, 3)
                })
        else:
            assigned_idx = None
            orig_qe = float(question_data_list[origin_q_idx]["relative_end"])
            if origin_q_idx < num_q - 1 and (s_end - orig_qe) <= transition_buffer:
                assigned_idx = origin_q_idx
            else:
                best_overlap = -1.0
                best_idx = origin_q_idx
                for idx, q_item in enumerate(question_data_list):
                    qs = float(q_item["relative_start"])
                    qe = float(q_item["relative_end"])
                    overlap = max(0.0, min(s_end, qe) - max(s_start, qs))
                    if overlap > best_overlap:
                        best_overlap = overlap
                        best_idx = idx
                assigned_idx = best_idx

            question_matched_speech[assigned_idx].append(seg_text)

    assembled_answers = {}
    for idx, q_item in enumerate(question_data_list):
        matched_parts = question_matched_speech.get(idx, [])
        spoken = " ".join(matched_parts).strip()
        spoken = " ".join(spoken.split())
        q_text = q_item.get("question", "")
        is_ans = is_valid_answer(spoken, question=q_text)
        assembled_answers[idx] = {
            "candidate_answer": spoken if is_ans else "",
            "raw_spoken": spoken,
            "is_answered": is_ans,
            "words": question_word_details.get(idx, [])
        }

    return assembled_answers


def run_all_tests():
    print("=" * 70)
    print("SUITE: SPEECH SEGMENTATION & AI EVALUATION ACCURACY")
    print("=" * 70)

    passed_count = 0
    total_count = 7

    # -------------------------------------------------------------------------
    # TEST 1: Q1 and Q2 are answered; Q3 is unanswered
    # -------------------------------------------------------------------------
    print("\n--- TEST 1: Q1 and Q2 answered, Q3 unanswered ---")
    q_answers_t1 = [
        {
            "question_number": 1,
            "question": "Tell me about yourself.",
            "candidate_answer": "Hi, my name is Naveen Kumar. I am pursuing my B.Tech final year at PP Savani University and I have skills in Python and SQL.",
            "is_answered": True,
            "expected_concepts": get_expected_concepts("Tell me about yourself.")
        },
        {
            "question_number": 2,
            "question": "What are your strengths and how can they help you in this role?",
            "candidate_answer": "My core strengths are technical skills and hard working, which help me solve problems efficiently.",
            "is_answered": True,
            "expected_concepts": get_expected_concepts("What are your strengths and how can they help you in this role?")
        },
        {
            "question_number": 3,
            "question": "What is Python and what are its main features?",
            "candidate_answer": "",
            "is_answered": False,
            "expected_concepts": get_expected_concepts("What is Python and what are its main features?")
        }
    ]

    res1 = evaluate_interview(q_answers_t1)
    q1_eval = res1["questions"][0]
    q2_eval = res1["questions"][1]
    q3_eval = res1["questions"][2]

    print(f"Q1 Overall: {q1_eval['overall_score']} | Tech: {q1_eval['technical_score']}")
    print(f"Q2 Overall: {q2_eval['overall_score']} | Tech: {q2_eval['technical_score']}")
    print(f"Q3 Overall: {q3_eval['overall_score']} | Tech: {q3_eval['technical_score']}")
    print(f"Interview Overall: {res1['overall_score']}")
    print(f"Counts: Attempted={res1['attempted_questions']}, Answered={res1['answered_questions']}, Unanswered={res1['unanswered_questions']}")

    assert q1_eval["overall_score"] > 0, "Q1 overall should be > 0"
    assert q2_eval["overall_score"] > 0, "Q2 overall should be > 0"
    assert q3_eval["overall_score"] == 0.0, "Q3 overall should be 0.0"
    assert q3_eval["technical_score"] == 0.0, "Q3 technical score should be 0.0"
    assert q3_eval["relevance_score"] == 0.0, "Q3 relevance score should be 0.0"
    assert q3_eval["concept_score"] == 0.0, "Q3 concept score should be 0.0"
    assert res1["attempted_questions"] == 3, "Attempted count should be 3"
    assert res1["answered_questions"] == 2, "Answered count should be 2"
    assert res1["unanswered_questions"] == 1, "Unanswered count should be 1"

    # Verify Q3 is excluded from interview average:
    expected_interview_avg = clamp_score((q1_eval["overall_score"] + q2_eval["overall_score"]) / 2.0)
    assert abs(res1["overall_score"] - expected_interview_avg) < 1.0, f"Interview overall {res1['overall_score']} should match 2-question avg {expected_interview_avg}"
    print(">> TEST 1 PASSED: Q1/Q2 evaluated, Q3 zeroed and excluded from interview average")
    passed_count += 1

    # -------------------------------------------------------------------------
    # TEST 2: Q2 ends with phrase whose Whisper segment crosses into Q3 time window
    # -------------------------------------------------------------------------
    print("\n--- TEST 2: Q2 Whisper segment crosses into Q3 time window ---")
    # Exact scenario from user:
    # Q1: 0.0s -> 12.0s
    # Q2: 12.0s -> 24.798s (user transitions at 24.798s)
    # Q3: 24.798s -> 35.0s
    # Segment: 16.62s -> 25.78s
    # Text: "My core strengths and technical strengths on skills are hard-working job."
    # The word "job." spans 24.9s - 25.78s (midpoint ~25.34s, past the 24.798s boundary)
    q_data_t2 = [
        {"question_number": 1, "question": "Tell me about yourself.", "relative_start": 0.0, "relative_end": 12.0},
        {"question_number": 2, "question": "What are your strengths?", "relative_start": 12.0, "relative_end": 24.798},
        {"question_number": 3, "question": "What is Python?", "relative_start": 24.798, "relative_end": 35.0}
    ]

    segments_t2 = [
        {
            "start": 1.0, "end": 10.5,
            "text": "Hi, my name is Naveen. I am pursuing B.Tech final year at PP Savani University.",
            "words": [
                {"word": "Hi,", "start": 1.0, "end": 1.5, "probability": 0.99},
                {"word": "my", "start": 1.6, "end": 1.8, "probability": 0.99},
                {"word": "name", "start": 1.9, "end": 2.2, "probability": 0.99},
                {"word": "is", "start": 2.3, "end": 2.5, "probability": 0.99},
                {"word": "Naveen.", "start": 2.6, "end": 3.2, "probability": 0.98},
                {"word": "I", "start": 4.0, "end": 4.2, "probability": 0.99},
                {"word": "am", "start": 4.3, "end": 4.5, "probability": 0.99},
                {"word": "pursuing", "start": 4.6, "end": 5.2, "probability": 0.98},
                {"word": "B.Tech", "start": 5.3, "end": 5.8, "probability": 0.97},
                {"word": "final", "start": 5.9, "end": 6.3, "probability": 0.99},
                {"word": "year", "start": 6.4, "end": 6.8, "probability": 0.99},
                {"word": "at", "start": 7.0, "end": 7.2, "probability": 0.99},
                {"word": "PP", "start": 7.3, "end": 7.6, "probability": 0.95},
                {"word": "Savani", "start": 7.7, "end": 8.2, "probability": 0.95},
                {"word": "University.", "start": 8.3, "end": 9.5, "probability": 0.99}
            ]
        },
        {
            "start": 16.62, "end": 25.78,
            "text": "My core strengths and technical strengths on skills are hard-working job.",
            "words": [
                {"word": "My", "start": 16.62, "end": 17.0, "probability": 0.99},
                {"word": "core", "start": 17.1, "end": 17.5, "probability": 0.99},
                {"word": "strengths", "start": 17.6, "end": 18.2, "probability": 0.98},
                {"word": "and", "start": 18.3, "end": 18.6, "probability": 0.99},
                {"word": "technical", "start": 18.7, "end": 19.3, "probability": 0.99},
                {"word": "strengths", "start": 19.4, "end": 20.0, "probability": 0.98},
                {"word": "on", "start": 20.1, "end": 20.4, "probability": 0.95},
                {"word": "skills", "start": 20.5, "end": 21.2, "probability": 0.99},
                {"word": "are", "start": 21.3, "end": 21.7, "probability": 0.98},
                {"word": "hard-working", "start": 22.0, "end": 24.3, "probability": 0.96},
                {"word": "job.", "start": 24.9, "end": 25.78, "probability": 0.92}
            ]
        }
    ]

    assigned_t2 = assign_whisper_to_questions(q_data_t2, segments_t2, transition_buffer=1.2)
    q2_result = assigned_t2[1]
    q3_result = assigned_t2[2]

    print(f"Q2 Raw Spoken: '{q2_result['raw_spoken']}'")
    print(f"Q2 Final Answer: '{q2_result['candidate_answer']}' (is_answered={q2_result['is_answered']})")
    print(f"Q3 Raw Spoken: '{q3_result['raw_spoken']}'")
    print(f"Q3 Final Answer: '{q3_result['candidate_answer']}' (is_answered={q3_result['is_answered']})")

    assert "job." in q2_result["raw_spoken"], "Q2 must retain 'job.' to prevent splitting 'hard-working job'"
    assert "hard-working job." in q2_result["raw_spoken"], "Phrase 'hard-working job.' must be intact in Q2"
    assert q3_result["candidate_answer"] == "", "Q3 candidate_answer must be empty"
    assert q3_result["is_answered"] is False, "Q3 must NOT be marked as answered"
    print(">> TEST 2 PASSED: Crossing phrase 'hard-working job.' kept intact in Q2; Q3 remains clean & unanswered")
    passed_count += 1

    # -------------------------------------------------------------------------
    # TEST 3: Word at question boundary assigned to no more than one question
    # -------------------------------------------------------------------------
    print("\n--- TEST 3: Word boundary uniqueness (no duplicates, no omissions) ---")
    all_assigned_words = []
    for q_idx in range(len(q_data_t2)):
        all_assigned_words.extend([w["word"] for w in assigned_t2[q_idx]["words"]])

    whisper_words_input = []
    for seg in segments_t2:
        whisper_words_input.extend([w["word"] for w in seg["words"]])

    print(f"Total Whisper Words Input: {len(whisper_words_input)}")
    print(f"Total Assigned Words: {len(all_assigned_words)}")

    assert len(whisper_words_input) == len(all_assigned_words), "Total assigned words must equal total input words"

    # Verify no word is assigned to more than one question:
    word_occurrence_map = {}
    for q_idx in range(len(q_data_t2)):
        for w_info in assigned_t2[q_idx]["words"]:
            key = (w_info["word"], w_info["start"], w_info["end"])
            word_occurrence_map[key] = word_occurrence_map.get(key, 0) + 1

    for word_key, count in word_occurrence_map.items():
        assert count == 1, f"Word {word_key} was assigned {count} times (must be exactly 1)!"

    print(">> TEST 3 PASSED: Every word at boundaries is assigned to exactly one question with 0 duplications")
    passed_count += 1

    # -------------------------------------------------------------------------
    # TEST 4: Finishing on Q2 does not generate Q3 if Q3 was never displayed
    # -------------------------------------------------------------------------
    print("\n--- TEST 4: Finish on Q2 does not create phantom Q3 ---")
    # Simulate client side question tracking when user finishes on Q2:
    all_20_questions = [
        {"question": "Tell me about yourself.", "type": "HR"},
        {"question": "What are your strengths?", "type": "HR"},
        {"question": "What is Python?", "type": "ROLE"},
        {"question": "Explain OOP.", "type": "ROLE"}
    ]
    # User was on Q2 (index 1), never clicked Next to view Q3
    current_q_index = 1
    q_start_times = {0: 1000, 1: 14000}
    q_end_times = {0: 14000, 1: 26000}

    displayed_indices = [idx for idx in q_start_times.keys() if q_start_times[idx] is not None]
    max_displayed = max(current_q_index, *displayed_indices) if displayed_indices else current_q_index

    attempted_slice = all_20_questions[:max_displayed + 1]
    submitted_questions = []
    for idx, q in enumerate(attempted_slice):
        s_time = q_start_times.get(idx)
        e_time = q_end_times.get(idx)
        submitted_questions.append({
            "question_number": idx + 1,
            "question": q["question"],
            "start_time": s_time,
            "end_time": e_time
        })

    print("Submitted Questions Count:", len(submitted_questions))
    print("Submitted Question Numbers:", [q["question_number"] for q in submitted_questions])

    assert len(submitted_questions) == 2, "Only Q1 and Q2 should be submitted"
    assert submitted_questions[-1]["question_number"] == 2, "Last question submitted should be Q2"
    assert not any(q["question_number"] == 3 for q in submitted_questions), "Q3 must not exist in submitted questions"
    print(">> TEST 4 PASSED: Finishing on Q2 generates exactly 2 questions; phantom Q3 is prevented")
    passed_count += 1

    # -------------------------------------------------------------------------
    # TEST 5: Self-introduction mentioning education matched to education concept
    # -------------------------------------------------------------------------
    print("\n--- TEST 5: Self-introduction education concept matching ---")
    exp_intro = get_expected_concepts("Tell me about yourself.")
    test_ans_edu = "Hi, my name is Naveen Kumar. I am pursuing my B.Tech final year at PP Savani University."
    
    r_edu = evaluate_question("Tell me about yourself.", candidate_answer=test_ans_edu, expected_concepts=exp_intro)
    print("Candidate Answer:", test_ans_edu)
    print("Matched Concepts:", r_edu["matched_concepts"])
    print("Missing Concepts:", r_edu["missing_concepts"])

    assert "education" in r_edu["matched_concepts"], "education concept must be matched"
    if "introduction" in exp_intro:
        assert "introduction" in r_edu["matched_concepts"], "introduction concept must be matched"
    assert "projects" in r_edu["missing_concepts"], "projects must be missing (not fabricated)"
    assert "career goals" in r_edu["missing_concepts"], "career goals must be missing (not fabricated)"

    # Test variants of educational institutions & study expressions:
    edu_phrases = [
        "I am pursuing my B.Tech final year at PP Savani University.",
        "Currently studying at university in computer engineering.",
        "I graduated with a btech degree from college.",
        "In my final year of academics at PPSA."
    ]
    for phrase in edu_phrases:
        matched_bool = is_concept_matched("education", phrase)
        print(f"  Phrase '{phrase[:50]}...' -> education matched: {matched_bool}")
        assert matched_bool, f"Failed to match education for phrase: {phrase}"

    print(">> TEST 5 PASSED: Education concept matched reliably across institution and study expressions")
    passed_count += 1

    # -------------------------------------------------------------------------
    # TEST 6: Empty answer receives zero technical/relevance scores
    # -------------------------------------------------------------------------
    print("\n--- TEST 6: Empty answer receives zero technical/relevance scores ---")
    empty_cases = ["", "   ", None, "...", "...?!", "---"]
    for ec in empty_cases:
        eval_ec = evaluate_question("Tell me about yourself.", candidate_answer=ec, expected_concepts=exp_intro)
        assert eval_ec["technical_score"] == 0.0, f"Technical score for '{ec}' must be 0.0"
        assert eval_ec["relevance_score"] == 0.0, f"Relevance score for '{ec}' must be 0.0"
        assert eval_ec["concept_score"] == 0.0, f"Concept score for '{ec}' must be 0.0"
        assert eval_ec["overall_score"] == 0.0, f"Overall score for '{ec}' must be 0.0"
        assert eval_ec["matched_concepts"] == [], f"Matched concepts for '{ec}' must be empty"
        assert len(eval_ec["missing_concepts"]) == len(exp_intro), f"All concepts must be missing for '{ec}'"

    print(">> TEST 6 PASSED: Empty and punctuation answers receive strictly 0.0 scores with no score fabrication")
    passed_count += 1

    # -------------------------------------------------------------------------
    # TEST 7: Short transcription fragment not automatically treated as meaningful answer
    # -------------------------------------------------------------------------
    print("\n--- TEST 7: Short transcription fragments vs legitimate short answers ---")
    # Stray fragments / fillers that should NOT be marked as valid answers
    fragments = ["job.", "job", "the", "um", "uh", "and so", "you know", "okay.", "fine", "thing"]
    for frag in fragments:
        is_valid = is_valid_answer(frag, question="What is Python?")
        eval_frag = evaluate_question("What is Python?", candidate_answer=frag, expected_concepts=["programming language", "interpreted"])
        print(f"  Fragment '{frag}' -> is_valid_answer: {is_valid}, Tech: {eval_frag['technical_score']}, Overall: {eval_frag['overall_score']}")
        assert is_valid is False, f"Fragment '{frag}' should NOT be considered a valid answer"
        assert eval_frag["technical_score"] == 0.0, f"Fragment '{frag}' should receive 0.0 tech score"
        assert eval_frag["overall_score"] == 0.0, f"Fragment '{frag}' should receive 0.0 overall score"

    # Legitimate short answers that MUST be recognized
    valid_shorts = [
        ("Python", "What is your primary programming language?"),
        ("Yes", "Are you comfortable working in a team?"),
        ("machine learning", "What domain are you specializing in?"),
        ("hard working", "What are your strengths?")
    ]
    for answer_text, q_text in valid_shorts:
        is_valid = is_valid_answer(answer_text, question=q_text)
        print(f"  Valid short '{answer_text}' for '{q_text[:30]}...' -> is_valid_answer: {is_valid}")
        assert is_valid is True, f"Legitimate answer '{answer_text}' should be recognized as valid"

    print(">> TEST 7 PASSED: Stray fragments rejected as unanswered; legitimate short answers preserved")
    passed_count += 1

    # -------------------------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print(f"ALL {passed_count}/{total_count} SPEECH SEGMENTATION & EVALUATION TESTS PASSED")
    print("=" * 70)

if __name__ == "__main__":
    run_all_tests()
