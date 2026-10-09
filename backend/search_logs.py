import os

brain_dir = r"C:\Users\User\.gemini\antigravity-ide\brain"
for conv in os.listdir(brain_dir):
    logs_dir = os.path.join(brain_dir, conv, ".system_generated", "logs")
    if os.path.exists(logs_dir):
        for f in os.listdir(logs_dir):
            if f.endswith(".jsonl"):
                p = os.path.join(logs_dir, f)
                try:
                    with open(p, "r", encoding="utf-8", errors="ignore") as fl:
                        for idx, line in enumerate(fl, 1):
                            if "InterviewAnswers" in line:
                                print(f"{conv} / {f}:{idx}")
                                break
                except Exception:
                    pass
