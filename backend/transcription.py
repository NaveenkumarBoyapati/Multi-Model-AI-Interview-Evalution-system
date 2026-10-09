from faster_whisper import WhisperModel
import os


# ============================================
# WHISPER MODEL (SINGLETON)
# ============================================

MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base.en")
DEFAULT_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "en")

def get_initial_prompt(role=None):
    """
    Returns domain-tuned vocabulary prompts for Faster-Whisper based on interview role.
    Significantly improves recognition of technical tools (Tableau, SQL, Power BI, FastAPI, JUnit),
    framework names, degrees, and common phrasing without hallucination.
    """
    role_lower = str(role or "").lower().strip()
    if "data" in role_lower:
        return (
            "Job interview for Data Analyst. Degree: B.Tech final year, P.P. Savani University. "
            "I did projects like multimodal interview evaluation, face evaluation, drowsiness detection. "
            "My skills are Python, SQL, Power BI, Excel, Tableau. "
            "Core strengths and technical skills: communication, being motivated, helping others, problem solving. "
            "Data analysis, data cleaning, data visualization, business intelligence."
        )
    elif "web" in role_lower:
        return (
            "Job interview for Web Developer. Degree: B.Tech final year, P.P. Savani University. "
            "I did projects like responsive web portals, frontend applications. "
            "My skills are HTML5, CSS3, JavaScript, React, RESTful APIs, responsive web design, media queries. "
            "Core strengths and technical skills: communication, problem solving, teamwork, being motivated."
        )
    elif "java" in role_lower:
        return (
            "Job interview for Java Developer. Degree: B.Tech final year, P.P. Savani University. "
            "I did projects like backend services, web applications. "
            "My skills are Java, Spring Boot, Hibernate, JUnit, OOP, multithreading, SQL. "
            "Core strengths and technical skills: communication, problem solving, team player, being motivated."
        )
    elif "python" in role_lower:
        return (
            "Job interview for Python Developer. Degree: B.Tech final year, P.P. Savani University. "
            "I did projects like REST APIs, backend services, data processing. "
            "My skills are Python, Django, Flask, FastAPI, OOP, MRO, C3 linearization, SQL. "
            "Core strengths and technical skills: communication, analytical problem solving, being motivated."
        )
    return (
        "Job interview. Degree: B.Tech final year, P.P. Savani University. "
        "I did projects like software development, data analysis, web applications. "
        "My skills are Python, Java, SQL, Excel, Tableau, Power BI. "
        "Core strengths and technical skills: communication, being motivated, helping others, problem solving."
    )

INTERVIEW_INITIAL_PROMPT = get_initial_prompt()

print(f"Loading Faster-Whisper model ({MODEL_SIZE}) on CPU (int8)...")

model = WhisperModel(
    MODEL_SIZE,
    device="cpu",
    compute_type="int8"
)

print("Faster-Whisper model loaded successfully.")


# ============================================
# TRANSCRIBE RECORDING
# ============================================

def transcribe_recording(file_path, role=None):
    """
    Transcribes an audio/video recording once and returns the full transcript
    along with precise segment timestamps for question-wise mapping.
    Uses role-aware vocabulary prompting to maximize domain accuracy.
    """
    if not os.path.exists(file_path):
        return {
            "success": False,
            "text": "",
            "language": None,
            "segments": [],
            "error": "Recording file not found"
        }

    try:
        print(f"\n[Whisper STT] Processing recording: {os.path.basename(file_path)} (Role: {role})")
        prompt = get_initial_prompt(role)

        segments_generator, info = model.transcribe(
            file_path,
            language=DEFAULT_LANGUAGE,
            initial_prompt=prompt,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
            condition_on_previous_text=False,
            word_timestamps=True
        )

        transcript_parts = []
        detailed_segments = []

        for segment in segments_generator:
            text = segment.text.strip()
            if text:
                transcript_parts.append(text)
                seg_dict = {
                    "start": round(segment.start, 3),
                    "end": round(segment.end, 3),
                    "text": text,
                    "words": []
                }
                if segment.words:
                    for w in segment.words:
                        w_text = w.word.strip()
                        if w_text:
                            seg_dict["words"].append({
                                "start": round(w.start, 3),
                                "end": round(w.end, 3),
                                "word": w_text,
                                "probability": round(w.probability, 3)
                            })
                detailed_segments.append(seg_dict)

        transcript = " ".join(transcript_parts).strip()

        print(f"[Whisper STT] Complete. Detected language: {info.language}")
        print(f"[Whisper STT] Extracted {len(detailed_segments)} speech segments.")
        print(f"[Whisper STT] Preview: {transcript[:120]}...\n" if len(transcript) > 120 else f"[Whisper STT] Transcript: {transcript}\n")

        return {
            "success": True,
            "text": transcript,
            "language": info.language,
            "segments": detailed_segments
        }

    except Exception as error:
        print(f"[Whisper STT Error] {error}")
        return {
            "success": False,
            "text": "",
            "language": None,
            "segments": [],
            "error": str(error)
        }