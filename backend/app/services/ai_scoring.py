import os
import librosa
import numpy as np
from faster_whisper import WhisperModel
from app.database import SessionLocal
from app import models


# ==============================
# FFMPEG PATH
# ==============================

if os.name == "nt":
    os.environ["PATH"] += os.pathsep + r"C:\ffmpeg-8.0.1-essentials_build\bin"


# ==============================
# LOAD WHISPER MODEL
# ==============================

model = None

def get_model():
    global model

    if model is None:
        print("Loading Faster-Whisper model...")

        model = WhisperModel(
            "base",
            device="cpu",
            compute_type="int8"
        )

        print("Whisper model loaded")

    return model


# ==============================
# LANGUAGE TOOL
# ==============================

tool = None
try:
    import language_tool_python
    tool = language_tool_python.LanguageTool("en-US")
    print("LanguageTool initialized")
except Exception as e:
    print("LanguageTool not available (grammar checking will use basic rules):", e)


# ==============================
# SILENCE DETECTION
# ==============================

def is_silent(audio_path, threshold=0.01):

    try:
        y, sr = librosa.load(audio_path)
        volume = np.mean(np.abs(y))
        return volume < threshold

    except:
        return False


# ==============================
# AUDIO DURATION
# ==============================

def get_audio_duration(audio_path):

    try:
        duration = librosa.get_duration(path=audio_path)
        print(f"Audio duration: {duration:.2f}s")
        return duration

    except:
        return None


# ==============================
# TRANSCRIPTION
# ==============================

def transcribe_audio(audio_path):

    print("\n===== STARTING TRANSCRIPTION =====")

    if is_silent(audio_path):
        print("Silent audio detected")
        return "", 0

    model = get_model()

    segments, info = model.transcribe(audio_path, beam_size=5)

    text = ""

    for segment in segments:
        text += segment.text + " "

    text = text.strip()

    duration = get_audio_duration(audio_path)

    print("Transcription:", text)
    print("===== TRANSCRIPTION COMPLETE =====\n")

    return text, duration


# ==============================
# ANSWER EVALUATION
# ==============================

def evaluate_answer(question, answer, audio_duration=None, answer_type="audio"):

    print("\n===== STARTING ANSWER EVALUATION =====")
    print("Answer:", answer)

    if not answer or not answer.strip():
        return {
            "grammar_score": 0,
            "fluency_score": 0,
            "final_score": 0,
            "grammar_errors": 0,
            "feedback": "No speech detected.",
            "word_count": 0
        }

    word_count = len(answer.split())

    grammar_errors = 0
    grammar_score = 5

    if tool:
        try:
            matches = tool.check(answer)
            grammar_errors = len(matches)

            error_ratio = grammar_errors / word_count if word_count else 0

            if error_ratio == 0:
                grammar_score = 10
            elif error_ratio <= 0.1:
                grammar_score = 8
            elif error_ratio <= 0.2:
                grammar_score = 6
            else:
                grammar_score = 4

        except:
            grammar_score = 5


    if answer_type == "audio":
        fluency = calculate_speaking_fluency(answer, word_count, audio_duration)
        final_score = round((fluency * 0.6) + (grammar_score * 0.4))
    else:
        fluency = calculate_writing_fluency(answer, word_count)
        final_score = round((fluency * 0.5) + (grammar_score * 0.5))


    feedback = generate_feedback(word_count, grammar_errors, fluency)

    return {
        "grammar_score": grammar_score,
        "fluency_score": fluency,
        "final_score": final_score,
        "grammar_errors": grammar_errors,
        "feedback": feedback,
        "word_count": word_count
    }


# ==============================
# SPEAKING FLUENCY
# ==============================

def calculate_speaking_fluency(text, word_count, audio_duration):

    score = 0

    if word_count < 5:
        score += 1
    elif word_count < 15:
        score += 3
    else:
        score += 5

    if audio_duration and word_count:
        wpm = (word_count / audio_duration) * 60

        if 90 <= wpm <= 160:
            score += 3
        else:
            score += 1

    return min(10, score)


# ==============================
# WRITING FLUENCY
# ==============================

def calculate_writing_fluency(text, word_count):

    score = 0

    if word_count < 5:
        score += 1
    elif word_count < 20:
        score += 4
    else:
        score += 6

    sentences = text.split(".")

    if len(sentences) > 2:
        score += 2

    return min(10, score)


# ==============================
# FEEDBACK
# ==============================

def generate_feedback(word_count, grammar_errors, fluency):

    feedback = []

    if fluency >= 8:
        feedback.append("Excellent response.")
    elif fluency >= 6:
        feedback.append("Good response.")
    else:
        feedback.append("Needs improvement.")

    if grammar_errors == 0:
        feedback.append("Grammar is excellent.")
    elif grammar_errors <= 3:
        feedback.append("Minor grammar issues.")
    else:
        feedback.append("Multiple grammar mistakes.")

    if word_count < 10:
        feedback.append("Try to speak more.")

    return " ".join(feedback)


# ==============================
# AUDIO BACKGROUND SCORING
# ==============================

def process_ai_scoring(answer_id, question_text, audio_path):

    db = SessionLocal()

    try:

        transcript, duration = transcribe_audio(audio_path)

        evaluation = evaluate_answer(
            question_text,
            transcript,
            audio_duration=duration,
            answer_type="audio"
        )

        answer = db.query(models.QuestionAnswer).filter(
            models.QuestionAnswer.id == answer_id
        ).first()

        if answer:

            answer.transcribed_text = transcript
            answer.final_score = evaluation["final_score"]
            answer.grammar_score = evaluation["grammar_score"]
            answer.fluency_score = evaluation["fluency_score"]
            answer.word_count = evaluation["word_count"]
            answer.feedback = evaluation["feedback"]

            db.commit()

    except Exception as e:
        print("AI scoring error:", e)

    finally:
        db.close()


# ==============================
# TEXT BACKGROUND SCORING
# ==============================

def process_text_scoring(answer_id, question_text, text_answer):

    db = SessionLocal()

    try:

        evaluation = evaluate_answer(
            question_text,
            text_answer,
            audio_duration=0,
            answer_type="text"
        )

        answer = db.query(models.QuestionAnswer).filter(
            models.QuestionAnswer.id == answer_id
        ).first()

        if answer:

            answer.transcribed_text = text_answer
            answer.final_score = evaluation["final_score"]
            answer.grammar_score = evaluation["grammar_score"]
            answer.fluency_score = evaluation["fluency_score"]
            answer.word_count = evaluation["word_count"]
            answer.feedback = evaluation["feedback"]

            db.commit()

    except Exception as e:
        print("Text scoring error:", e)

    finally:
        db.close()