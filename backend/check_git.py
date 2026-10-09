import os
import subprocess

git_dirs = [
    r"C:\Program Files\Git\cmd\git.exe",
    r"C:\Program Files\Git\bin\git.exe",
    r"C:\Users\User\AppData\Local\Programs\Git\bin\git.exe",
    r"C:\Users\User\AppData\Local\Programs\Git\cmd\git.exe"
]

git_exe = None
for gd in git_dirs:
    if os.path.exists(gd):
        git_exe = gd
        break

print("Git exe:", git_exe)
if git_exe and os.path.exists(r"d:\Nani Personal\multi model another work\.git"):
    res = subprocess.run([git_exe, "log", "-n", "10", "--oneline"], cwd=r"d:\Nani Personal\multi model another work", capture_output=True, text=True)
    print("Git log:\n", res.stdout)
