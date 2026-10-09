import os

root_dir = r"d:\Nani Personal\multi model another work"
for dp, dn, fns in os.walk(root_dir):
    if any(k in dp for k in [".git", "venv", "uploads", "__pycache__"]):
        continue
    for f in fns:
        p = os.path.join(dp, f)
        try:
            with open(p, "r", encoding="utf-8", errors="ignore") as fl:
                content = fl.read()
                if "InterviewAnswers" in content:
                    print(f"Match in {p}")
        except Exception:
            pass
