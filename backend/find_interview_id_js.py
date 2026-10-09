import os

root_dir = r"d:\Nani Personal\multi model another work\js"
for f in os.listdir(root_dir):
    if f.endswith(".js"):
        p = os.path.join(root_dir, f)
        with open(p, "r", encoding="utf-8", errors="ignore") as file:
            for i, line in enumerate(file, 1):
                if "interviewid" in line.lower():
                    print(f"{f}:{i} -> {line.strip()[:100]}")
