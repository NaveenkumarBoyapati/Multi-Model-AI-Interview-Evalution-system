"""
Test with current candidate (User 31):
1. Initial: 34 total interviews, 15 valid completed interviews, 15 progression points.
2. Complete 1 new interview -> 35 total interviews, 16 valid scored interviews, 16 progression points.
3. Terminate 1 interview -> 36 total interviews, 16 valid scored interviews, 16 progression points (no point added).
4. Clean up test records and restore to 34 total.
"""

import sys
import os
import json
import urllib.request
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import get_connection

token = 'G7hiu_rb3sF3LDY1oy473L4IVGWDIzOHfQ1mJnDVLpo'

def get_summary():
    req = urllib.request.Request(
        'http://127.0.0.1:8000/api/dashboard/summary',
        headers={'Authorization': f'Bearer {token}'}
    )
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read().decode())

def run():
    print("Testing dynamic updates with current candidate (User 31)...")

    # Step 1: Initial state
    s1 = get_summary()
    print("Step 1 - Initial State:")
    print(f"  Total Interviews: {s1['total_interviews']}")
    print(f"  Score Progression Points: {len(s1['score_progression'])}")
    assert s1['total_interviews'] == 34
    assert len(s1['score_progression']) == 15

    # Step 2: Complete a NEW normal interview
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Interviews (user_id, role, overall_score, technical_score, communication_score,
                               confidence_score, problem_solving_score, relevance_score, status,
                               created_at, completed_at, total_questions)
        VALUES (31, 'Data Analyst', 85.0, 80.0, 85.0, 85.0, 90.0, 85.0, 'COMPLETED', GETUTCDATE(), GETUTCDATE(), 5)
    """)
    conn.commit()
    cursor.execute("SELECT @@IDENTITY")
    new_comp_id = int(cursor.fetchone()[0])
    print(f"\nStep 2 - Inserted new completed interview #{new_comp_id}")

    s2 = get_summary()
    print(f"  Total Interviews: {s2['total_interviews']}")
    print(f"  Score Progression Points: {len(s2['score_progression'])}")
    print(f"  Latest Score: {s2['latest_score']}%")
    assert s2['total_interviews'] == 35, f"Expected 35, got {s2['total_interviews']}"
    assert len(s2['score_progression']) == 16, f"Expected 16, got {len(s2['score_progression'])}"
    assert s2['score_progression'][-1]['score'] == 85.0

    # Step 3: Create a Terminated interview
    cursor.execute("""
        INSERT INTO Interviews (user_id, role, overall_score, status, created_at, total_questions, terminated_reason)
        VALUES (31, 'Data Analyst', NULL, 'Terminated', GETUTCDATE(), 5, 'Security Tab Switch')
    """)
    conn.commit()
    cursor.execute("SELECT @@IDENTITY")
    new_term_id = int(cursor.fetchone()[0])
    print(f"\nStep 3 - Inserted new terminated interview #{new_term_id}")

    s3 = get_summary()
    print(f"  Total Interviews: {s3['total_interviews']}")
    print(f"  Score Progression Points: {len(s3['score_progression'])}")
    print(f"  Latest Score: {s3['latest_score']}%")
    assert s3['total_interviews'] == 36, f"Expected 36, got {s3['total_interviews']}"
    assert len(s3['score_progression']) == 16, f"Expected 16 (terminated excluded), got {len(s3['score_progression'])}"
    assert s3['latest_score'] == 85.0, f"Latest score must remain valid score (85.0), got {s3['latest_score']}"

    # Clean up the 2 test interview rows
    cursor.execute("DELETE FROM Interviews WHERE id IN (?, ?)", (new_comp_id, new_term_id))
    conn.commit()
    print("\nStep 4 - Cleaned up test interview records.")

    s4 = get_summary()
    print(f"  Restored Total Interviews: {s4['total_interviews']}")
    print(f"  Restored Score Progression Points: {len(s4['score_progression'])}")
    assert s4['total_interviews'] == 34
    assert len(s4['score_progression']) == 15

    cursor.close()
    conn.close()
    print("\nALL REAL-DATA TESTS PASSED PERFECTLY!")

if __name__ == "__main__":
    run()
