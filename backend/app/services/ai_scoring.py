"""Local English practice scoring. Not a calibrated proficiency examination."""
import logging
import re
from functools import lru_cache
from threading import Lock

import av
import numpy as np
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)
_model_lock = Lock()
_tool_lock = Lock()
MAX_AUDIO_SECONDS = 300
SAMPLE_RATE = 16000
RUBRIC = "practice-v1"


@lru_cache(maxsize=1)
def get_model():
    return WhisperModel("base", device="cpu", compute_type="int8", cpu_threads=2, num_workers=1)


@lru_cache(maxsize=1)
def get_language_tool():
    import language_tool_python
    # Fixed version ensures cache lookup matches the downloaded distribution.
    return language_tool_python.LanguageTool("en-US", language_tool_download_version="6.6")


def decode_audio_file(path, max_seconds=MAX_AUDIO_SECONDS):
    """Decode supported browser formats with a duration cap before allocating a full clip."""
    chunks, total = [], 0
    try:
        with av.open(str(path)) as container:
            resampler = av.AudioResampler(format="s16", layout="mono", rate=SAMPLE_RATE)
            for frame in container.decode(audio=0):
                for converted in resampler.resample(frame):
                    total += converted.samples
                    if total > max_seconds * SAMPLE_RATE:
                        raise ValueError(f"Audio must be at most {max_seconds} seconds")
                    chunks.append(converted.to_ndarray().flatten())
            for converted in resampler.resample(None):
                total += converted.samples
                if total > max_seconds * SAMPLE_RATE:
                    raise ValueError(f"Audio must be at most {max_seconds} seconds")
                chunks.append(converted.to_ndarray().flatten())
    except (av.FFmpegError, IndexError) as exc:
        raise ValueError("The audio file cannot be decoded") from exc
    if total < SAMPLE_RATE // 4:
        raise ValueError("Record at least a quarter second of audio")
    return np.concatenate(chunks).astype(np.float32) / 32768.0


def is_silent(audio_path, threshold=0.001):
    samples = decode_audio_file(audio_path)
    return float(np.sqrt(np.mean(samples ** 2))) < threshold


def get_audio_duration(audio_path):
    return len(decode_audio_file(audio_path)) / SAMPLE_RATE


def transcribe_audio(audio_path):
    samples = decode_audio_file(audio_path)
    duration = len(samples) / SAMPLE_RATE
    if float(np.sqrt(np.mean(samples ** 2))) < 0.001:
        return "", duration
    with _model_lock:
        segments, _ = get_model().transcribe(
            samples, language="en", beam_size=5, vad_filter=True,
            condition_on_previous_text=False,
        )
        transcript = " ".join(segment.text.strip() for segment in segments).strip()
    return transcript, duration


def calculate_speaking_fluency(text, word_count, audio_duration):
    # A practice proxy based on response length and speaking pace, not pronunciation.
    if not word_count or not audio_duration or audio_duration <= 0:
        return 0
    length_score = min(6, word_count / 5)
    wpm = word_count * 60 / audio_duration
    pace_score = max(0, 4 - abs(wpm - 125) / 40)
    return round(min(10, length_score + pace_score), 1)


def calculate_writing_fluency(text, word_count):
    if not word_count:
        return 0
    sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
    return round(min(10, min(6, word_count / 5) + min(4, len(sentences) * 2)), 1)


def generate_feedback(word_count, grammar_errors, fluency, answer_type="audio"):
    feedback = ["Response length and flow are strong." if fluency >= 7 else "Keep practicing response length and flow."]
    feedback.append("No grammar issues detected." if grammar_errors == 0 else f"Review the {grammar_errors} grammar or spelling issues detected.")
    if word_count < 10:
        feedback.append("Develop your answer with more detail.")
    if answer_type == "audio":
        feedback.append("Speaking fluency is estimated from length and pace.")
    return " ".join(feedback)


def evaluate_answer(question, answer, audio_duration=None, answer_type="audio"):
    words = re.findall(r"\b[\w]+(?:['’-][\w]+)*\b", answer or "")
    word_count = len(words)
    if not word_count:
        return {"grammar_score":0, "fluency_score":0, "final_score":0,
                "grammar_errors":0, "word_count":0,
                "feedback":"No speech detected." if answer_type == "audio" else "No written response provided."}
    # A dependency failure must not become a fabricated grammar score.
    with _tool_lock:
        tool = get_language_tool()
        if tool is None:
            raise RuntimeError("Grammar analysis is unavailable")
        matches = tool.check(answer)
    grammar_errors = len(matches)
    grammar_score = max(0, round(10 * (1 - min(1, 2 * grammar_errors / word_count))))
    if answer_type == "audio":
        fluency = calculate_speaking_fluency(answer, word_count, audio_duration)
        final = round(fluency * 0.6 + grammar_score * 0.4)
    else:
        fluency = calculate_writing_fluency(answer, word_count)
        final = round((fluency + grammar_score) / 2)
    # A one-word answer cannot earn a high overall score just for being grammatical.
    final = min(final, 3 if word_count < 5 else 6 if word_count < 10 else 10)
    return {"grammar_score":grammar_score, "fluency_score":fluency, "final_score":final,
            "grammar_errors":grammar_errors, "word_count":word_count,
            "feedback":generate_feedback(word_count, grammar_errors, fluency, answer_type)}
