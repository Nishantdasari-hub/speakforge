import { useEffect, useState, useRef, useCallback } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import { apiRequest } from "../api";

export default function TestDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [questions, setQuestions] = useState([]);
  const [attemptId, setAttemptId] = useState(null);
  const [current, setCurrent] = useState(0);
  const [timeLeft, setTimeLeft] = useState(0);
  const [text, setText] = useState("");
  const [audio, setAudio] = useState(null);
  const [audioUrl, setAudioUrl] = useState(null);
  const [recording, setRecording] = useState(false);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const recorder = useRef(null);
  const stream = useRef(null);
  const pendingAudio = useRef(null);
  const audioRef = useRef(null);
  const lock = useRef(false);
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
    let active = true;
    (async () => {
      try {
        const items = await apiRequest(`/tests/${id}/questions`);
        const attempt = await apiRequest(`/tests/${id}/start`, { method: "POST" });
        if (!active) return;
        const next = items.findIndex(q => !attempt.answered_question_ids.includes(q.id));
        setQuestions(items);
        setAttemptId(attempt.attempt_id);
        setCurrent(next === -1 ? items.length : next);
      } catch (err) {
        if (active) setError(err.message);
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
      mounted.current = false;
      if (recorder.current?.state === "recording") recorder.current.stop();
      stream.current?.getTracks().forEach(track => track.stop());
    };
  }, [id]);

  const stopRecording = useCallback(async () => {
    if (recorder.current?.state === "recording") recorder.current.stop();
    // MediaRecorder emits its final data asynchronously. Wait before uploading.
    const blob = pendingAudio.current ? await pendingAudio.current : audioRef.current;
    stream.current?.getTracks().forEach(track => track.stop());
    return blob;
  }, []);

  useEffect(() => {
    setTimeLeft(questions[current]?.time_limit || 0);
  }, [current, questions]);

  useEffect(() => {
    if (timeLeft <= 0 || busy) return;
    const timer = setTimeout(() => setTimeLeft(left => Math.max(0, left - 1)), 1000);
    return () => clearTimeout(timer);
  }, [timeLeft, busy]);

  useEffect(() => {
    if (timeLeft === 0 && recording) stopRecording();
  }, [timeLeft, recording, stopRecording]);

  useEffect(() => {
    if (!audio) { setAudioUrl(null); return; }
    const url = URL.createObjectURL(audio);
    setAudioUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [audio]);

  const startRecording = async () => {
    if (lock.current) return;
    setError("");
    lock.current = true;
    setBusy(true);
    try {
      if (!navigator.mediaDevices?.getUserMedia) throw new Error("Recording requires HTTPS and a supported browser.");
      const media = await navigator.mediaDevices.getUserMedia({ audio: true });
      if (!mounted.current) { media.getTracks().forEach(track => track.stop()); return; }
      stream.current = media;
      const mimeType = ["audio/webm;codecs=opus", "audio/mp4", "audio/webm"].find(type => MediaRecorder.isTypeSupported(type));
      const value = new MediaRecorder(media, mimeType ? { mimeType } : undefined);
      recorder.current = value;
      const chunks = [];
      audioRef.current = null;
      setAudio(null);
      pendingAudio.current = new Promise(resolve => {
        value.ondataavailable = event => { if (event.data.size) chunks.push(event.data); };
        value.onstop = () => {
          const blob = new Blob(chunks, { type: value.mimeType });
          audioRef.current = blob;
          media.getTracks().forEach(track => track.stop());
          if (mounted.current) { setAudio(blob); setRecording(false); }
          resolve(blob);
        };
        value.onerror = () => {
          media.getTracks().forEach(track => track.stop());
          if (mounted.current) { setRecording(false); setError("Recording failed. Please record again."); }
          resolve(null);
        };
      });
      if (timeLeft === 0) setTimeLeft(questions[current].time_limit);
      value.start();
      setRecording(true);
    } catch (err) {
      pendingAudio.current = null;
      recorder.current = null;
      stream.current?.getTracks().forEach(track => track.stop());
      setError(err.name === "NotAllowedError" ? "Microphone access was denied. Allow access and try again." : err.message);
    } finally {
      lock.current = false;
      if (mounted.current) setBusy(false);
    }
  };

  const submit = async () => {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError("");
    try {
      const question = questions[current];
      if (question) {
        const form = new FormData();
        form.append("attempt_id", attemptId);
        if (question.question_type === "audio") {
          const blob = await stopRecording();
          if (!blob?.size) throw new Error("Record an answer before continuing.");
          form.append("audio", blob, "answer.audio");
        } else {
          if (!text.trim()) throw new Error("Write an answer before continuing.");
          form.append("text_answer", text.trim());
        }
        await apiRequest(`/tests/submit-answer/${question.id}`, { method:"POST", body:form });
      }
      if (current >= questions.length - 1) {
        setCurrent(questions.length);
        await apiRequest(`/tests/${id}/submit?attempt_id=${attemptId}`, { method:"POST" });
        navigate(`/report/${id}?attempt=${attemptId}`);
      } else {
        setCurrent(index => index + 1);
        setText("");
        setAudio(null);
        audioRef.current = null;
        pendingAudio.current = null;
      }
    } catch (err) {
      setError(err.message); // Keep the answer intact so a failed upload can be retried.
    } finally {
      lock.current = false;
      if (mounted.current) setBusy(false);
    }
  };

  const question = questions[current];
  return <main className="min-h-screen bg-gray-950 text-white flex justify-center p-6">
    <section className="w-full max-w-2xl my-auto bg-gray-900 rounded-xl p-8 space-y-6">
      <Link to="/dashboard" className="text-blue-400">Back to Dashboard</Link>
      <h1 className="text-3xl font-bold">Speaking and Writing Practice</h1>
      {error && <p role="alert" className="text-red-300">{error}</p>}
      {loading ? <p>Loading questions...</p> : attemptId && <>
        {question ? <>
          <h2>Question {current + 1} / {questions.length}</h2>
          <p className="text-xl">{question.question_text}</p>
          <p role="timer">{timeLeft > 0 ? `${timeLeft}s remaining` : "Practice time ended. Review and submit your answer."}</p>
          {question.question_type === "text" ? <textarea aria-label="Your answer" maxLength={10000} rows={6} value={text} onChange={e => setText(e.target.value)} disabled={busy} className="w-full bg-gray-800 p-3 rounded" /> : <div className="space-y-4">
            <button onClick={recording ? stopRecording : startRecording} disabled={busy} className="bg-green-600 px-5 py-3 rounded">{recording ? "Stop Recording" : "Start Recording"}</button>
            {recording && <p role="status">Recording...</p>}
            {audioUrl && <audio controls src={audioUrl} className="w-full" />}
          </div>}
        </> : <p>All answers saved. Submit your test to start evaluation.</p>}
        <button onClick={submit} disabled={busy} className="bg-blue-600 disabled:opacity-50 px-6 py-3 rounded">{busy ? "Saving..." : current >= questions.length - 1 ? "Submit Test" : "Next Question"}</button>
      </>}
    </section>
  </main>;
}
