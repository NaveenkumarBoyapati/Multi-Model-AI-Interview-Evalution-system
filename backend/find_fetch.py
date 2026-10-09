with open(r"d:\Nani Personal\multi model another work\js\interview.js", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    if "fetch(" in line or "axios" in line or "XMLHttpRequest" in line or "/interview" in line or "/api" in line:
        print(f"interview.js:{i} -> {line.strip()[:100]}")
