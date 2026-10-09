import os

brain_dir = r"C:\Users\User\.gemini\antigravity-ide\brain"
for conv in os.listdir(brain_dir):
    conv_path = os.path.join(brain_dir, conv)
    if not os.path.isdir(conv_path):
        continue
    for root, dirs, files in os.walk(conv_path):
        for f in files:
            if f.endswith((".py", ".md", ".jsonl", ".txt")):
                p = os.path.join(root, f)
                try:
                    with open(p, "r", encoding="utf-8", errors="ignore") as fl:
                        for idx, line in enumerate(fl, 1):
                            if "InterviewAnswers" in line:
                                print(f"{conv} / {f}:{idx} -> {line.strip()[:120]}")
                                break
                except Exception:
                    pass
