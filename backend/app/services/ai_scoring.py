import whisper
import language_tool_python
import os
import librosa

# IMPORTANT: tell whisper where ffmpeg is
if os.name == 'nt':  
    os.environ["PATH"] += os.pathsep + r"C:\ffmpeg-8.0.1-essentials_build\bin"

# Load models
model = None
def get_model():
    global model
    if model is None:
        try:
            print("Loading Whisper model...")
            model = whisper.load_model("tiny")
            print("Whisper model loaded successfully")
        except Exception as e:
            print(f"Failed to load Whisper model: {e}")
            raise RuntimeError("Audio transcription unavailable due to model loading failure.")
    return model

# LanguageTool is initialized lazily: the first call downloads a large
# archive, which would otherwise block application startup.
tool = None
_tool_init_failed = False


def get_tool():
    global tool, _tool_init_failed
    if tool is None and not _tool_init_failed:
        try:
            print("Initializing LanguageTool...")
            tool = language_tool_python.LanguageTool('en-US')
            print("LanguageTool initialized successfully")
        except Exception as e:
            print(f"LanguageTool failed to initialize: {e}")
            print("Grammar checking will be disabled")
            _tool_init_failed = True
    return tool


def get_audio_duration(audio_path):
    """Get audio file duration using librosa"""
    try:
        duration = librosa.get_duration(filename=audio_path)
        print(f"Audio duration: {duration:.2f} seconds")
        return duration
    except Exception as e:
        print(f"Could not get audio duration: {e}")
        return None

def transcribe_audio(audio_path):

    print("\n===== STARTING TRANSCRIPTION =====")

    model = get_model()
    result = model.transcribe(audio_path)

    text = result["text"]
    duration = get_audio_duration(audio_path)

    print("Transcription Result:", text)
    print("===== TRANSCRIPTION COMPLETE =====\n")

    return text, duration


def evaluate_answer(question, answer, audio_duration=None, answer_type="audio"):
    
    print("\n===== STARTING ANSWER EVALUATION =====")
    print("Answer text:", repr(answer))
    print("Audio duration:", audio_duration)
    print("Answer type:", answer_type)
    
    # Check for very short audio duration (likely silent or failed recording) - only for audio
    if answer_type == "audio" and audio_duration and audio_duration < 1.0:
        print("🚨 DETECTED VERY SHORT AUDIO - LIKELY SILENT")
        return {
            "grammar_score": 0,
            "fluency_score": 0,
            "final_score": 0,
            "grammar_errors": 0,
            "feedback": "Recording too short. Please ensure you speak clearly and record for full duration.",
            "word_count": 0,
            "is_silent": True
        }
    
    # Check for empty/silent recording or empty text
    if not answer or not answer.strip() or len(answer.strip()) < 3:
        print("🚨 DETECTED SILENT/EMPTY RECORDING OR TEXT")
        return {
            "grammar_score": 0,
            "fluency_score": 0,
            "final_score": 0,
            "grammar_errors": 0,
            "feedback": "No speech detected. Please speak clearly and provide an answer to question." if answer_type == "audio" else "No text provided. Please write an answer to the question.",
            "word_count": 0,
            "is_silent": True
        }
    
    # Check for very short answers (likely not meaningful)
    if len(answer.strip()) < 5:
        print("⚠️ DETECTED VERY SHORT ANSWER")
        return {
            "grammar_score": 1,
            "fluency_score": 1,
            "final_score": 1,
            "grammar_errors": 0,
            "feedback": "Answer too short. Please provide a more complete response to the question.",
            "word_count": len(answer.split()),
            "is_silent": False
        }

    # Grammar checking (same for both audio and text)
    grammar_tool = get_tool()
    if grammar_tool is not None:
        try:
            matches = grammar_tool.check(answer)
            grammar_errors = len(matches)
            
            # Calculate grammar score based on error density
            word_count = len(answer.split())
            if word_count > 0:
                error_ratio = grammar_errors / word_count
                
                if error_ratio == 0:
                    grammar_score = 10  # Perfect grammar
                elif error_ratio <= 0.05:  # ≤5% error rate
                    grammar_score = 9   # Excellent grammar
                elif error_ratio <= 0.1:   # ≤10% error rate
                    grammar_score = 8   # Very good grammar
                elif error_ratio <= 0.15:  # ≤15% error rate
                    grammar_score = 7   # Good grammar
                elif error_ratio <= 0.2:   # ≤20% error rate
                    grammar_score = 6   # Adequate grammar
                elif error_ratio <= 0.3:   # ≤30% error rate
                    grammar_score = 4   # Poor grammar
                else:
                    grammar_score = 2   # Very poor grammar
            else:
                grammar_score = 0
                
        except Exception:
            grammar_errors = 0
            grammar_score = 5  # Default middle score if checking fails
            print("⚠️ Grammar checking failed, using default values")
    else:
        grammar_errors = 0
        grammar_score = 5  # Default middle score if tool unavailable
        print("⚠️ Grammar checking disabled")

    word_count = len(answer.split())
    
    # DIFFERENT FLUENCY SCORING BASED ON ANSWER TYPE
    if answer_type == "audio":
        fluency = calculate_speaking_fluency_score(answer, word_count, audio_duration)
    else:
        fluency = calculate_writing_fluency_score(answer, word_count)

    # Calculate final score with weighted average
    # Give more weight to fluency for speaking assessment, balanced for writing
    if answer_type == "audio":
        final_score = round((fluency * 0.6) + (grammar_score * 0.4))
    else:
        final_score = round((fluency * 0.5) + (grammar_score * 0.5))  # Balanced for writing
    
    # Determine performance level
    if final_score >= 9:
        performance_level = "Expert"
    elif final_score >= 8:
        performance_level = "Advanced"
    elif final_score >= 7:
        performance_level = "Upper-Intermediate"
    elif final_score >= 6:
        performance_level = "Intermediate"
    elif final_score >= 4:
        performance_level = "Beginner"
    elif final_score >= 2:
        performance_level = "Novice"
    else:
        performance_level = "Needs Improvement"

    # Enhanced feedback generation
    feedback = generate_enhanced_feedback(word_count, grammar_errors, fluency, answer, answer_type)

    print("Grammar Errors:", grammar_errors)
    print("Word Count:", word_count)
    print("Fluency Score:", fluency)
    print("Grammar Score:", grammar_score)
    print("Final Score:", final_score)
    print("Performance Level:", performance_level)

    return {
        "grammar_score": grammar_score,
        "fluency_score": fluency,
        "final_score": final_score,
        "performance_level": performance_level,
        "grammar_errors": grammar_errors,
        "feedback": feedback,
        "word_count": word_count
    }

def calculate_speaking_fluency_score(text, word_count, audio_duration=None):
    """Performance-based fluency scoring (0-10 scale) for speaking"""
    
    score = 0
    
    # Content Quality (0-3 points)
    if word_count == 0:
        content_score = 0
    elif word_count < 5:
        content_score = 0.5  # Very poor content
    elif word_count < 10:
        content_score = 1    # Poor content
    elif word_count < 20:
        content_score = 2    # Adequate content
    elif word_count < 40:
        content_score = 2.5  # Good content
    elif word_count < 60:
        content_score = 3    # Excellent content
    else:
        content_score = 2.5  # Too long, slight penalty
    
    score += content_score
    
    # Speaking Pace (0-2 points) - Only if audio duration available
    if audio_duration and audio_duration > 0 and word_count > 0:
        words_per_minute = (word_count / audio_duration) * 60
        
        if words_per_minute < 60:
            pace_score = 0    # Too slow
        elif words_per_minute < 90:
            pace_score = 0.5  # Slow
        elif words_per_minute <= 160:
            pace_score = 2    # Ideal pace (90-160 WPM)
        elif words_per_minute <= 180:
            pace_score = 1.5  # Slightly fast
        elif words_per_minute <= 200:
            pace_score = 1    # Fast
        else:
            pace_score = 0.5  # Too fast
        
        score += pace_score
    
    # Fluency & Coherence (0-2 points)
    text_lower = text.lower()
    
    # Count filler words and hesitations
    hesitation_words = [' um ', ' uh ', ' er ', ' ah ', ' hmm ', ' you know ', ' like ']
    hesitation_count = sum(text_lower.count(word) for word in hesitation_words)
    
    # Calculate hesitation ratio
    if word_count > 0:
        hesitation_ratio = hesitation_count / word_count
    else:
        hesitation_ratio = 1
    
    if hesitation_ratio > 0.3:  # More than 30% hesitations
        coherence_score = 0    # Very poor fluency
    elif hesitation_ratio > 0.2:
        coherence_score = 0.5  # Poor fluency
    elif hesitation_ratio > 0.1:
        coherence_score = 1    # Adequate fluency
    elif hesitation_ratio > 0.05:
        coherence_score = 1.5  # Good fluency
    else:
        coherence_score = 2    # Excellent fluency
    
    score += coherence_score
    
    # Sentence Structure (0-2 points)
    sentences = [s.strip() for s in text.split('.') if s.strip()]
    
    if len(sentences) == 0:
        structure_score = 0
    elif len(sentences) == 1:
        if len(sentences[0].split()) < 5:
            structure_score = 0  # Single very short sentence
        elif len(sentences[0].split()) < 10:
            structure_score = 0.5  # Single short sentence
        else:
            structure_score = 1  # Single adequate sentence
    elif len(sentences) <= 3:
        structure_score = 1.5  # Good sentence variety
    else:
        structure_score = 2    # Excellent sentence structure
    
    score += structure_score
    
    # Vocabulary Variety (0-1 point)
    words = text.lower().split()
    if word_count > 0:
        unique_ratio = len(set(words)) / word_count
        if unique_ratio > 0.8:
            vocab_score = 1  # Excellent vocabulary
        elif unique_ratio > 0.6:
            vocab_score = 0.7  # Good vocabulary
        elif unique_ratio > 0.4:
            vocab_score = 0.4  # Adequate vocabulary
        else:
            vocab_score = 0.1  # Poor vocabulary repetition
    else:
        vocab_score = 0
    
    score += vocab_score
    
    # Ensure score is within 0-10 range
    final_score = max(0, min(10, round(score, 1)))
    
    return final_score

def calculate_writing_fluency_score(text, word_count):
    """Writing fluency scoring (0-10 scale) - different from speaking fluency"""
    
    score = 0
    
    # Content Quality (0-3 points) - Same as speaking
    if word_count == 0:
        content_score = 0
    elif word_count < 5:
        content_score = 0.5  # Very poor content
    elif word_count < 10:
        content_score = 1    # Poor content
    elif word_count < 20:
        content_score = 2    # Adequate content
    elif word_count < 40:
        content_score = 2.5  # Good content
    elif word_count < 60:
        content_score = 3    # Excellent content
    else:
        content_score = 2.5  # Too long, slight penalty
    
    score += content_score
    
    # Writing Coherence & Structure (0-3 points) - Different from speaking
    sentences = [s.strip() for s in text.split('.') if s.strip()]
    
    if len(sentences) == 0:
        coherence_score = 0
    elif len(sentences) == 1:
        if word_count < 5:
            coherence_score = 0  # Single very short sentence
        elif word_count < 10:
            coherence_score = 0.5  # Single short sentence
        else:
            coherence_score = 1  # Single adequate sentence
    elif len(sentences) <= 3:
        coherence_score = 2  # Good sentence variety
    else:
        coherence_score = 3  # Excellent sentence structure
    
    score += coherence_score
    
    # Writing Organization (0-2 points) - New for writing
    # Check for logical flow indicators
    transition_words = ['however', 'therefore', 'moreover', 'furthermore', 'consequently', 'additionally', 'because', 'so', 'then', 'finally']
    transition_count = sum(1 for word in transition_words if word in text.lower())
    
    if transition_count >= 3:
        organization_score = 2  # Well organized
    elif transition_count >= 1:
        organization_score = 1  # Some organization
    else:
        organization_score = 0.5  # Limited organization
    
    score += organization_score
    
    # Vocabulary & Expression (0-2 points) - Same as speaking
    words = text.lower().split()
    if word_count > 0:
        unique_ratio = len(set(words)) / word_count
        if unique_ratio > 0.8:
            vocab_score = 2  # Excellent vocabulary
        elif unique_ratio > 0.6:
            vocab_score = 1.5  # Good vocabulary
        elif unique_ratio > 0.4:
            vocab_score = 1  # Adequate vocabulary
        else:
            vocab_score = 0.5  # Poor vocabulary repetition
    else:
        vocab_score = 0
    
    score += vocab_score
    
    # Ensure score is within 0-10 range
    final_score = max(0, min(10, round(score, 1)))
    
    return final_score

def generate_enhanced_feedback(word_count, grammar_errors, fluency, answer, answer_type="audio"):
    """Performance-based feedback with specific guidance"""
    
    feedback = []
    
    # Overall performance level
    if answer_type == "audio":
        if fluency >= 8:
            feedback.append("Excellent speaking performance! You demonstrate strong communication skills.")
        elif fluency >= 6:
            feedback.append("Good speaking performance with clear areas for improvement.")
        elif fluency >= 4:
            feedback.append("Your speaking needs focused improvement to reach proficiency.")
            feedback.append(" Your speaking needs focused improvement to reach proficiency.")
        else:
            feedback.append(" Significant practice needed to develop basic speaking skills.")
    else:  # text answers
        if fluency >= 8:
            feedback.append(" Excellent writing skills! Your text is well-structured and articulate.")
        elif fluency >= 6:
            feedback.append(" Good writing with room for improvement in organization.")
        elif fluency >= 4:
            feedback.append(" Your writing needs improvement in structure and clarity.")
        else:
            feedback.append(" Significant practice needed to develop basic writing skills.")
    
    # Content and length feedback
    if word_count == 0:
        if answer_type == "audio":
            feedback.append(" No response provided. Please speak and answer the question.")
        else:
            feedback.append(" No response provided. Please write and answer the question.")
    elif word_count < 5:
        feedback.append(" Response too brief. Provide at least 10-15 words for a complete answer.")
    elif word_count < 10:
        feedback.append("📝 Answer is too short. Aim for 15-25 words to fully address the question.")
    elif word_count > 80:
        feedback.append("🗣️ Answer is quite long. Practice being more concise while maintaining detail.")
    elif 20 <= word_count <= 50:
        feedback.append("✅ Good answer length with appropriate detail and focus.")
    
    # Grammar feedback with specific guidance
    if grammar_errors == 0:
        feedback.append("📚 Perfect grammar! Your sentence structure is excellent.")
    elif grammar_errors <= 2:
        feedback.append("📝 Minor grammar issues. Review basic sentence construction for improvement.")
    elif grammar_errors <= 5:
        feedback.append("⚠️ Several grammar mistakes. Focus on subject-verb agreement and tense consistency.")
    elif grammar_errors <= 10:
        feedback.append("🚨 Multiple grammar errors. Consider reviewing fundamental grammar rules.")
    else:
        feedback.append("❌ Major grammar issues. Recommend grammar lessons and practice exercises.")
    
    # Fluency-specific feedback
    answer_lower = answer.lower()
    
    # Check for specific fluency issues
    hesitation_count = sum(answer_lower.count(word) for word in [' um ', ' uh ', ' er ', ' ah ', ' hmm '])
    like_count = answer_lower.count(' like ')
    
    if hesitation_count > 5:
        feedback.append("🤔 Excessive hesitation detected. Practice speaking more confidently to reduce fillers.")
    elif hesitation_count > 2:
        feedback.append("🗣️ Noticeable hesitation. Try to pause briefly instead of using filler words.")
    
    if like_count > 4:
        feedback.append("💬 Overuse of 'like' as filler. Expand your vocabulary for better expression.")
    elif like_count > 2:
        feedback.append("📢 Moderate use of 'like'. Vary your language for more professional speech.")
    
    # Speaking pace guidance (if available from fluency analysis)
    if fluency < 5:
        feedback.append("⏱️ Work on your speaking pace - aim for steady, confident delivery.")
    elif fluency < 7:
        feedback.append("🎤 Good pace, but focus on smoother transitions between ideas.")
    
    # Sentence structure feedback
    sentences = [s.strip() for s in answer.split('.') if s.strip()]
    if len(sentences) == 1 and word_count > 20:
        feedback.append("📋 Consider breaking long responses into multiple sentences for clarity.")
    elif len(sentences) >= 4 and word_count < 30:
        feedback.append("🔗 Good use of multiple sentences! This shows structured thinking.")
    
    # Vocabulary variety encouragement
    words = answer_lower.split()
    if word_count > 0:
        unique_ratio = len(set(words)) / word_count
        if unique_ratio > 0.8:
            feedback.append("🎨 Excellent vocabulary variety! You express ideas with rich language.")
        elif unique_ratio < 0.4:
            feedback.append("📖 Expand your vocabulary by reading more and using varied word choices.")
    
    # Actionable next steps
    if fluency < 6:
        feedback.append("🎯 Practice tip: Record yourself speaking and listen for areas to improve.")
    
    if fluency >= 8 and grammar_errors <= 1:
        feedback.append("🏆 Outstanding performance! You're ready for advanced speaking challenges.")
    
    return " ".join(feedback)