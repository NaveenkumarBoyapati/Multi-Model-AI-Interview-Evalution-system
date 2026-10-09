import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import get_connection

def inspect_details():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            fk.name AS FK_name,
            tp.name AS ParentTable,
            cp.name AS ParentColumn,
            tr.name AS RefTable,
            cr.name AS RefColumn
        FROM sys.foreign_keys fk
        INNER JOIN sys.tables tp ON fk.parent_object_id = tp.object_id
        INNER JOIN sys.tables tr ON fk.referenced_object_id = tr.object_id
        INNER JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
        INNER JOIN sys.columns cp ON fkc.parent_object_id = cp.object_id AND fkc.parent_column_id = cp.column_id
        INNER JOIN sys.columns cr ON fkc.referenced_object_id = cr.object_id AND fkc.referenced_column_id = cr.column_id
    """)
    fks = cursor.fetchall()
    print("=== FOREIGN KEYS ===")
    for fk in fks:
        print(f"{fk[1]}.{fk[2]} -> {fk[3]}.{fk[4]} (Constraint: {fk[0]})")

    print("\n=== COLUMNS IN InterviewHistory ===")
    cursor.execute("SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'InterviewHistory'")
    for c in cursor.fetchall():
        print(f"  {c[0]} ({c[1]}, nullable={c[2]})")

    print("\n=== COLUMNS IN InterviewAnswers ===")
    cursor.execute("SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'InterviewAnswers'")
    for c in cursor.fetchall():
        print(f"  {c[0]} ({c[1]}, nullable={c[2]})")

    print("\n=== COLUMNS IN EvaluationResults ===")
    cursor.execute("SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'EvaluationResults'")
    for c in cursor.fetchall():
        print(f"  {c[0]} ({c[1]}, nullable={c[2]})")

    print("\n=== COLUMNS IN Feedback ===")
    cursor.execute("SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Feedback'")
    for c in cursor.fetchall():
        print(f"  {c[0]} ({c[1]}, nullable={c[2]})")

    print("\n=== COLUMNS IN Interviews ===")
    cursor.execute("SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Interviews'")
    for c in cursor.fetchall():
        print(f"  {c[0]} ({c[1]}, nullable={c[2]})")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    inspect_details()
