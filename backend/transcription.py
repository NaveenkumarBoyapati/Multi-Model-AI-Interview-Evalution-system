from faster_whisper import WhisperModel
import os
import time
import numpy as np
import av
from typing import Dict, Any, Optional, Tuple, List


# ============================================
# WHISPER MODEL CONFIGURATION & INITIALIZATION
# ============================================

# Default to small.en for superior accuracy on Indian English and domain terminology,
# with automatic fallback to base.en if needed.
MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "small.en").strip()
DEFAULT_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "en").strip()

print(f"[Whisper STT] Initializing Faster-Whisper model ({MODEL_SIZE}) on CPU (compute_type=int8)...")
try:
    model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
    ACTIVE_MODEL_NAME = MODEL_SIZE
    print(f"[Whisper STT] Model '{MODEL_SIZE}' loaded successfully.")
except Exception as load_err:
    print(f"[Whisper STT Warning] Failed to load '{MODEL_SIZE}': {load_err}. Falling back to 'base.en'...")
    model = WhisperModel("base.en", device="cpu", compute_type="int8")
    ACTIVE_MODEL_NAME = "base.en"
    print("[Whisper STT] Fallback model 'base.en' loaded successfully.")


# ============================================
# AUDIO EXTRACTION & PREPROCESSING (PyAV / FFmpeg)
# ============================================

def extract_audio_pcm(file_path: str, target_sr: int = 16000) -> Tuple[Optional[np.ndarray], float, float]:
    """
    Extracts audio from WebM / MP4 / WAV container to a normalized float32 mono PCM array
    at 16,000 Hz using in-process FFmpeg (PyAV).
    Preserves original recording file completely intact.
    Returns: (audio_pcm_array, file_audio_duration_seconds, extraction_duration_seconds)
    """
    t0 = time.time()
    if not os.path.exists(file_path):
        return None, 0.0, 0.0

    try:
        container = av.open(file_path)
        audio_streams = [s for s in container.streams if s.type == "audio"]
        if not audio_streams:
            container.close()
            return None, 0.0, round(time.time() - t0, 3)

        astream = audio_streams[0]
        resampler = av.AudioResampler(format="fltp", layout="mono", rate=target_sr)
        chunks = []
        for frame in container.decode(astream):
            resampled_frames = resampler.resample(frame)
            if resampled_frames:
                for rf in resampled_frames:
                    chunks.append(rf.to_ndarray()[0])
        container.close()

        if not chunks:
            return None, 0.0, round(time.time() - t0, 3)

        audio_pcm = np.concatenate(chunks).astype(np.float32)
        duration_sec = round(len(audio_pcm) / float(target_sr), 3)
        extract_time = round(time.time() - t0, 3)
        return audio_pcm, duration_sec, extract_time

    except Exception as err:
        print(f"[Audio Extraction Error] Failed to decode audio from {os.path.basename(file_path)}: {err}")
        return None, 0.0, round(time.time() - t0, 3)


try:
    from env_loader import load_env
except ImportError:
    try:
        from backend.env_loader import load_env
    except ImportError:
        def load_env(override=False):
            return {}

load_env()

# ============================================
# VOCABULARY PROMPTS (KEYWORD & ENTITY TUNING)
# ============================================

def is_usable_candidate_name(name: Optional[str]) -> bool:
    """
    Validates whether candidate_name represents a realistic full name rather than
    a short username, system nickname, or generic placeholder (e.g., 'Nani', 'User', 'Admin', '12').
    Biasing Faster-Whisper with a short handle causes speech decoding to misrecognize or hallucinate
    the candidate's actual spoken name.
    """
    if not name or not isinstance(name, str):
        return False
    clean = name.strip()
    if not clean or len(clean) < 3:
        return False
    if clean.lower() in (
        "candidate", "the candidate", "user", "admin", "test", "tester",
        "nani", "kumar", "null", "none", "system administrator", "unit test", "smoke tester"
    ):
        return False
    parts = [p for p in clean.split() if len(p) > 1]
    return len(parts) >= 2


def get_initial_prompt(role: Optional[str] = None, candidate_name: Optional[str] = None) -> str:
    """
    Returns natural, contextual prompt text for Faster-Whisper based on interview role and candidate.
    Forms a coherent grammatical sentence that biases technical terms, acronyms, and proper nouns
    (such as 'B.Tech', 'P.P. Savani University', role keywords) without triggering hallucination loops.
    """
    if is_usable_candidate_name(candidate_name):
        candidate_subject = f"Candidate {candidate_name.strip()}"
    else:
        candidate_subject = "The candidate"

    role_str = (role or "Software Developer").strip()
    role_lower = role_str.lower()

    # Common portfolio project terms frequently mentioned in candidate introductions
    project_context = "academic projects including drowsiness detection, face digitisation, and multimodal AI interview evaluation"

    if "data" in role_lower:
        domain_skills = "Python, SQL, Excel, Power BI, Tableau, pandas, NumPy, data cleaning, and data visualization"
    elif "web" in role_lower:
        domain_skills = "HTML5, CSS3, JavaScript, React, Node.js, REST APIs, frontend, backend, and responsive web design"
    elif "java" in role_lower:
        domain_skills = "Java, Spring Boot, OOP, Hibernate, REST APIs, multithreading, SQL, Maven, and microservices"
    elif "python" in role_lower:
        domain_skills = "Python, Django, FastAPI, Flask, OOP, MRO, SQL, REST APIs, asyncio, data structures, algorithms, and data tools such as Power BI and Excel"
    else:
        domain_skills = "software engineering, programming, SQL databases, problem solving, and communication skills"

    return (
        f"Technical job interview for {role_str}. {candidate_subject} discusses education (B.Tech at P.P. Savani University), "
        f"{project_context}, strengths, and technical concepts including {domain_skills}."
    )

INTERVIEW_INITIAL_PROMPT = get_initial_prompt()


# ============================================
# TRANSCRIBE RECORDING
# ============================================

def transcribe_recording(file_path: str, role: Optional[str] = None, candidate_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Transcribes an audio/video recording once and returns the full transcript
    along with precise segment timestamps for question-wise mapping.
    Uses in-process PyAV audio extraction and natural sentence vocabulary prompting to maximize domain accuracy.
    """
    if not os.path.exists(file_path):
        return {
            "success": False,
            "text": "",
            "language": None,
            "segments": [],
            "error": "Recording file not found"
        }

    file_size_bytes = os.path.getsize(file_path)
    file_size_kb = round(file_size_bytes / 1024.0, 1)
    base_name = os.path.basename(file_path)

    print(f"\n[Whisper STT] Processing recording: {base_name} ({file_size_kb} KB)")
    print(f"[Whisper STT] Model: {ACTIVE_MODEL_NAME} | Role: {role or 'General'} | Candidate: {candidate_name or 'Unspecified'}")

    try:
        # Step 1: Extract 16kHz mono float32 PCM audio via PyAV
        audio_pcm, audio_duration, extract_dur = extract_audio_pcm(file_path, target_sr=16000)

        # Audio source: pass numpy float32 PCM array directly, or fallback to file_path
        audio_input = audio_pcm if (audio_pcm is not None and len(audio_pcm) > 0) else file_path

        # Step 2: Configure language handling appropriately
        if ACTIVE_MODEL_NAME.endswith(".en"):
            transcribe_lang = "en"
        else:
            transcribe_lang = None if DEFAULT_LANGUAGE.lower() in ("auto", "none", "") else DEFAULT_LANGUAGE

        prompt = get_initial_prompt(role=role, candidate_name=candidate_name)

        t_trans_start = time.time()
        # Clean Faster-Whisper decoding with:
        # 1. temperature=0.0: Prevents expensive multi-pass temperature fallback loops on CPU.
        # 2. repetition_penalty=1.1: Penalizes token loops (e.g. repeated sentence fragments).
        # 3. no_repeat_ngram_size=3: Directly prevents identical 3-gram runaway loops while preserving natural speech.
        segments_generator, info = model.transcribe(
            audio_input,
            language=transcribe_lang,
            initial_prompt=prompt,
            beam_size=5,
            temperature=0.0,
            repetition_penalty=1.1,
            no_repeat_ngram_size=3,
            vad_filter=True,
            vad_parameters=dict(
                threshold=0.5,
                min_silence_duration_ms=800,
                speech_pad_ms=400
            ),
            condition_on_previous_text=False,
            compression_ratio_threshold=2.4,
            no_speech_threshold=0.6,
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

        t_trans_end = time.time()
        trans_duration = round(t_trans_end - t_trans_start, 2)
        transcript = " ".join(transcript_parts).strip()
        word_count = sum(len(s.get("words", [])) for s in detailed_segments)

        # Step 3: Diagnostic logs (no credentials or tokens logged)
        print(f"[Whisper STT] Audio extracted duration: {audio_duration:.2f}s (extraction took {extract_dur:.3f}s)")
        print(f"[Whisper STT] Transcription duration: {trans_duration:.2f}s | Detected language: {info.language}")
        print(f"[Whisper STT] Extracted {len(detailed_segments)} speech segments ({word_count} words).")
        print(f"[Whisper STT] Preview: {transcript[:120]}...\n" if len(transcript) > 120 else f"[Whisper STT] Transcript: {transcript}\n")

        return {
            "success": True,
            "text": transcript,
            "language": info.language,
            "segments": detailed_segments,
            "audio_duration": audio_duration,
            "transcription_duration": trans_duration,
            "model": ACTIVE_MODEL_NAME
        }

    except Exception as error:
        print(f"[Whisper STT Error] Failed transcribing {base_name}: {type(error).__name__}: {error}")
        return {
            "success": False,
            "text": "",
            "language": None,
            "segments": [],
            "error": str(error)
        }