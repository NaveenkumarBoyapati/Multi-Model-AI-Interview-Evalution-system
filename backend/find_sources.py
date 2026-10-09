import os

def find_keywords():
    root = r"d:\Nani Personal"
    keywords = ["InterviewAnswers", "InterviewHistory", "EvaluationResults", "question_id", "start_ms", "end_ms"]
    
    for dirpath, dirnames, filenames in os.walk(root):
        if any(skip in dirpath for skip in [".git", "venv", "node_modules", "uploads", "__pycache__"]):
            continue
        for f in filenames:
            ext = os.path.splitext(f)[1].lower()
            if ext in [".py", ".sql", ".js", ".txt", ".md", ".json"]:
                p = os.path.join(dirpath, f)
                try:
                    with open(p, "r", encoding="utf-8", errors="ignore") as fl:
                        content = fl.read()
                        matches = [k for k in keywords if k in content]
                        if matches:
                            print(f"File {p} matched: {matches}")
                except Exception as e:
                    pass

if __name__ == "__main__":
    find_keywords()
