import sys
import importlib

packages = [
    "sentence_transformers",
    "torch",
    "sklearn",
    "spacy",
    "nltk",
    "numpy",
    "fastapi",
    "faster_whisper",
    "pyodbc"
]

results = {}
for pkg in packages:
    try:
        importlib.import_module(pkg)
        results[pkg] = "INSTALLED"
    except Exception as e:
        results[pkg] = f"NOT INSTALLED: {e}"

with open("env_check_result.txt", "w") as f:
    for k, v in results.items():
        f.write(f"{k}: {v}\n")
    f.write(f"\nPython executable: {sys.executable}\n")
    f.write(f"Python version: {sys.version}\n")
