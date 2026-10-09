import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from question_bank import generate_fallback_concepts, get_expected_concepts

def test_fallback_quality():
    q1 = "How would you explain a distributed ledger to an executive?"
    c1 = generate_fallback_concepts(q1)
    print(f"Fallback for '{q1}':\n  {c1}")
    assert "implementation" not in " ".join(c1).lower(), f"Unexpected 'implementation' in fallback: {c1}"
    assert "explanation" in " ".join(c1).lower()

    q2 = "Difference between monolithic and microservice architecture"
    c2 = generate_fallback_concepts(q2)
    print(f"Fallback for '{q2}':\n  {c2}")
    assert "implementation" not in " ".join(c2).lower()
    assert "distinctions" in " ".join(c2).lower() or "definitions" in " ".join(c2).lower()

    q3 = "What is WebAssembly and its runtime environment?"
    c3 = generate_fallback_concepts(q3)
    print(f"Fallback for '{q3}':\n  {c3}")
    assert "implementation" not in " ".join(c3).lower()

    print(">> All fallback quality tests passed successfully!")

if __name__ == "__main__":
    test_fallback_quality()
