"""Local English practice scoring. Not a calibrated proficiency examination."""
import logging
import re
from dataclasses import dataclass
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
RUBRIC = "practice-v2"


@dataclass(frozen=True)
class GrammarIssue:
    offset: int
    length: int
    message: str
    replacement: str = ""


# Narrow agreement checks supplement LanguageTool, which can miss these inside
# long, unpunctuated speech transcripts. These do not assess meaning/relevance.
_AGREEMENT_RULES = (
    (r"\b(I|you|we|they)\s+(does|has)\b", {"does":"do", "has":"have"}),
    (r"\b(we|they|you)\s+(is|was)\b", {"is":"are", "was":"were"}),
    (r"\bI\s+(is|are)\b", {"is":"am", "are":"am"}),
    (r"\b(he|she|it)\s+(think|mean|want|know|need|work|have|do)\b",
     {"think":"thinks", "mean":"means", "want":"wants", "know":"knows",
      "need":"needs", "work":"works", "have":"has", "do":"does"}),
)


def supplemental_grammar_issues(text):
    issues = []
    for pattern, replacements in _AGREEMENT_RULES:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            prefix = text[:match.start()]
            # Auxiliary inversion and subjunctives use the base verb legitimately:
            # "Does he think...?", "I suggest that she work...", "if I were you".
            if re.search(r"\b(?:do|does|did|can|could|will|would|shall|should|may|might|must)\s*$", prefix, re.I):
                continue
            if re.search(r"\b(?:suggest|recommend|request|insist|require|demand|important|essential)\b[^.!?]*$", prefix, re.I):
                continue
            start, end = match.span(match.lastindex)
            issues.append(GrammarIssue(start, end-start, "Check subject–verb agreement.",
                                       replacements[match.group(match.lastindex).lower()]))
    for match in re.finditer(r"\bmore\s+(better|worse)\b", text, re.I):
        issues.append(GrammarIssue(match.start(), len(match.group()),
                                   "Use a single comparative.", match.group(1)))
    return issues


def collect_grammar_issues(text, matches):
    issues = [GrammarIssue(m.offset, m.error_length, m.message,
                           m.replacements[0] if m.replacements else "") for m in matches]
    for issue in supplemental_grammar_issues(text):
        if not any(issue.offset < other.offset + other.length and
                   other.offset < issue.offset + issue.length for other in issues):
            issues.append(issue)
    return sorted(issues, key=lambda issue: issue.offset)


def calculate_grammar_score(errors, word_count):
    # Every detected issue has a fixed penalty plus a density penalty. Capping
    # the denominator prevents a long transcript from washing errors away.
    if not word_count:
        return 0
    penalty = errors * (0.75 + 25 / min(word_count, 100))
    return max(0, round(10 - penalty))


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


def generate_feedback(word_count, grammar_errors, fluency, answer_type="audio", issues=(), text=""):
    feedback = ["Response length and pace meet the practice target." if fluency >= 7 else "Keep practicing response length and pace."]
    feedback.append("No grammar issues detected." if grammar_errors == 0 else f"Review the {grammar_errors} grammar or spelling issues detected.")
    if word_count < 10:
        feedback.append("Develop your answer with more detail.")
    if answer_type == "audio":
        feedback.append("Length and pace do not establish coherent or accurate speech. Transcription can change spoken mistakes; compare the transcript with your recording.")
    for issue in issues[:4]:
        excerpt = text[issue.offset:issue.offset + issue.length][:80]
        suggestion = f' Suggested correction: “{issue.replacement[:80]}”.' if issue.replacement else ""
        feedback.append(f'“{excerpt}”: {issue.message}{suggestion}')
    if len(issues) > 4:
        feedback.append(f"Plus {len(issues)-4} additional detected issues.")
    feedback.append(f"Rubric: {RUBRIC}. Automated checks can miss errors and do not assess relevance or pronunciation.")
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
    issues = collect_grammar_issues(answer, matches)
    grammar_errors = len(issues)
    grammar_score = calculate_grammar_score(grammar_errors, word_count)
    if answer_type == "audio":
        fluency = calculate_speaking_fluency(answer, word_count, audio_duration)
        final = round(fluency * 0.3 + grammar_score * 0.7)
    else:
        fluency = calculate_writing_fluency(answer, word_count)
        final = round(fluency * 0.3 + grammar_score * 0.7)
    # Meeting length/pace targets must not erase detected language errors.
    final = min(final, grammar_score if grammar_errors else 10)
    # A one-word answer cannot earn a high overall score just for being grammatical.
    final = min(final, 3 if word_count < 5 else 6 if word_count < 10 else 10)
    return {"grammar_score":grammar_score, "fluency_score":fluency, "final_score":final,
            "grammar_errors":grammar_errors, "word_count":word_count,
            "feedback":generate_feedback(word_count, grammar_errors, fluency, answer_type, issues, answer)}
