import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from faster_whisper import WhisperModel

file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads", "Data_Analyst_20261004_221941_763267.webm")

model = WhisperModel("base.en", device="cpu", compute_type="int8")

role_prompt = (
    "Job interview for Data Analyst. Degree: B.Tech, P.P. Savani University. "
    "I did projects like multimodal interview evaluation, face evaluation, drowsiness detection. "
    "My skills are Python, Power BI, SQL, Excel, Tableau, data visualization. "
    "Core strengths and technical skills as well as communication."
)

print(f"Testing role-aware prompt on {os.path.basename(file_path)}...")
segments, info = model.transcribe(
    file_path,
    language="en",
    initial_prompt=role_prompt,
    beam_size=5,
    vad_filter=True,
    vad_parameters=dict(min_silence_duration_ms=500),
    condition_on_previous_text=False,
    word_timestamps=True
)

full_text = []
for s in segments:
    print(f"[{s.start:.2f}s - {s.end:.2f}s] {s.text}")
    full_text.append(s.text.strip())

combined = " ".join(full_text)
print("\nCombined Transcript:")
print(repr(combined))

# Check for key target terms
print("\nChecks:")
print("  'Tableau' in transcript:", "Tableau" in combined or "tableau" in combined.lower())
print("  'Diablo' in transcript:", "diablo" in combined.lower())
print("  'skills are' in transcript:", "skills are" in combined.lower())
print("  'skill serve' in transcript:", "skill serve" in combined.lower())
print("  'projects' in transcript:", "projects" in combined.lower())
