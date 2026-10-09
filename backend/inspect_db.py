import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database import get_connection

def inspect_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Get all tables
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
    tables = [r[0] for r in cursor.fetchall()]
    print("========================================")
    print("TABLES IN AIInterviewDB:", tables)
    print("========================================")

    for t in tables:
        print(f"\n--- TABLE: {t} ---")
        cursor.execute(f"SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{t}'")
        cols = cursor.fetchall()
        for c in cols:
            print(f"  {c[0]} ({c[1]}, nullable={c[2]}, max_len={c[3]})")

    # Let's inspect Foreign Keys
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
    print("\n========================================")
    print("FOREIGN KEYS:")
    print("========================================")
    for fk in fks:
        print(f"  {fk[0]}: {fk[1]}.{fk[2]} -> {fk[3]}.{fk[4]}")

    # Inspect records in tables mentioned by the user:
    # InterviewHistory, InterviewAnswers, EvaluationResults, Interviews
    for target in ["InterviewHistory", "InterviewAnswers", "EvaluationResults", "Interviews"]:
        if target in tables:
            print(f"\n========================================")
            print(f"SAMPLE ROWS IN {target}:")
            print("========================================")
            cursor.execute(f"SELECT TOP 10 * FROM {target} ORDER BY 1 DESC")
            col_names = [column[0] for column in cursor.description]
            print("COLUMNS:", col_names)
            rows = cursor.fetchall()
            for r in rows:
                print("ROW:", dict(zip(col_names, r)))

    # Inspect Interview 40 and 45 specifically across tables
    print("\n========================================")
    print("RECORDS FOR INTERVIEWS 39, 40, 44, 45:")
    print("========================================")
    for t in tables:
        # Check if table has interview_id or id
        cursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{t}'")
        t_cols = [c[0] for c in cursor.fetchall()]
        id_col = None
        if "interview_id" in t_cols:
            id_col = "interview_id"
        elif "id" in t_cols:
            id_col = "id"

        if id_col:
            cursor.execute(f"SELECT * FROM {t} WHERE {id_col} IN (39, 40, 44, 45)")
            col_names = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            if rows:
                print(f"\n--- {t} matches (by {id_col}) ---")
                for r in rows:
                    print(" ", dict(zip(col_names, r)))

    cursor.close()
    conn.close()

if __name__ == "__main__":
    inspect_db()
