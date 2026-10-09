# ===================================================
# TEST SEMANTIC EVALUATION ENGINE
# ===================================================

from evaluation import evaluate_question, evaluate_interview
from question_bank import get_expected_concepts

def run_test():
    print("========================================")
    print("TEST: Semantic Answer Evaluation")
    print("========================================")

    q = "What is normalization in SQL?"
    expected = get_expected_concepts(q)
    print("Question:", q)
    print("Expected Concepts:", expected)

    candidate_answer = "Normalization is used to organize database tables and reduce duplicate data."
    print("Candidate Answer:", candidate_answer)

    result = evaluate_question(
        question=q,
        candidate_answer=candidate_answer,
        expected_concepts=expected
    )

    print("\nResult:")
    print(f"Technical Score:      {result['technical_score']}%")
    print(f"Completeness Score:   {result['completeness_score']}%")
    print(f"Communication Score:  {result['communication_score']}%")
    print(f"Confidence Score:     {result['confidence_score']}%")
    print(f"Problem Solving:      {result['problem_solving_score']}%")
    print(f"Overall Score:        {result['overall_score']}/100")
    print("Matched Concepts:    ", result["matched_concepts"])
    print("Strengths:           ", result["strengths"])
    print("Improvements:        ", result["improvements"])
    print("========================================")

if __name__ == "__main__":
    run_test()
