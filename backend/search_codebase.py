import os

def search_files():
    root_dir = r"d:\Nani Personal\multi model another work"
    targets = ["CREATED", "InterviewAnswers", "status", "insert into"]
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if any(skip in dirpath for skip in [".git", "__pycache__", "venv", "node_modules", "uploads"]):
            continue
        for f in filenames:
            ext = os.path.splitext(f)[1].lower()
            if ext in [".py", ".js", ".html", ".sql", ".json", ".bat"]:
                filepath = os.path.join(dirpath, f)
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as file:
                        lines = file.readlines()
                        for i, line in enumerate(lines, 1):
                            for target in targets:
                                if target.lower() in line.lower():
                                    print(f"{os.path.relpath(filepath, root_dir)}:{i} [{target}]: {line.strip()[:100]}")
                except Exception as e:
                    pass

if __name__ == "__main__":
    search_files()
