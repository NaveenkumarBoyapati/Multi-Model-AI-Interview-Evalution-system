import os
from transcription import transcribe_recording

recording_path = r'D:\Nani Personal\multi model another work\backend\uploads\Web_Developer_20261004_202539_551213.webm'
res = transcribe_recording(recording_path)
print("Language:", res.get("language"))
print("Text:\n", res.get("text"))
print("\nSegments:")
for i, s in enumerate(res.get("segments", []), 1):
    print(f"Seg {i} [{s['start']:.2f} - {s['end']:.2f}]: '{s['text']}'")
    words_str = " ".join(f"{w['word']}[{w['start']}-{w['end']}]" for w in s.get("words", []))
    print(f"   Words: {words_str}")
