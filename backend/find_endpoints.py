with open(r"d:\Nani Personal\multi model another work\backend\main.py", "r", encoding="utf-8", errors="ignore") as f:
    for i, line in enumerate(f, 1):
        if line.strip().startswith("@app."):
            print(f"main.py:{i} -> {line.strip()}")
