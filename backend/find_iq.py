with open(r"d:\Nani Personal\multi model another work\js\interview.js", "r", encoding="utf-8", errors="ignore") as f:
    for i, line in enumerate(f, 1):
        if "interviewQuestions" in line:
            print(f"interview.js:{i} -> {line.strip()[:100]}")
