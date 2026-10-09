import os

def search_text():
    search_dirs = [
        r"C:\Users\User\.gemini\antigravity-ide\brain",
        r"C:\Users\User\Desktop",
        r"C:\Users\User\Downloads",
        r"d:\Nani Personal"
    ]
    target = "InterviewAnswers"
    for sdir in search_dirs:
        if not os.path.exists(sdir):
            continue
        for root, dirs, files in os.walk(sdir):
            # Skip virtualenvs or cache
            if any(k in root for k in ["venv", ".git", "__pycache__", "node_modules", "uploads"]):
                continue
            for f in files:
                if f.endswith((".py", ".sql", ".json", ".log", ".jsonl")):
                    p = os.path.join(root, f)
                    try:
                        with open(p, "r", encoding="utf-8", errors="ignore") as fl:
                            content = fl.read()
                            if target in content:
                                print(f"Found in: {p}")
                    except Exception:
                        pass

if __name__ == "__main__":
    search_text()
