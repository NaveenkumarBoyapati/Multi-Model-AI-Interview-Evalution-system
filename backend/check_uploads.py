import os
import glob

uploads_dir = r"d:\Nani Personal\multi model another work\backend\uploads"
files = glob.glob(os.path.join(uploads_dir, "*.webm"))
files.sort(key=os.path.getmtime, reverse=True)
print(f"Total webm files in uploads: {len(files)}")
for f in files[:5]:
    print(os.path.basename(f), os.path.getsize(f), "bytes")
