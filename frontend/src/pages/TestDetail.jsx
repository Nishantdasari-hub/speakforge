import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Swal from "sweetalert2";
import { motion } from "framer-motion";

function TestDetail() {

const { id } = useParams();
const navigate = useNavigate();

const [questions, setQuestions] = useState([]);
const [current, setCurrent] = useState(0);
const [timeLeft, setTimeLeft] = useState(30);

const [mediaRecorder, setMediaRecorder] = useState(null);
const [recording, setRecording] = useState(false);
const [recordingStartTime, setRecordingStartTime] = useState(null);
const [recordingDuration, setRecordingDuration] = useState(0);

const [audioBlob, setAudioBlob] = useState(null);
const [textAnswer, setTextAnswer] = useState("");

const [loadingAI, setLoadingAI] = useState(false);
const [isSubmitting, setIsSubmitting] = useState(false);

const token = localStorage.getItem("token");


// ---------------- LOAD QUESTIONS ----------------

useEffect(() => {

fetch(`http://127.0.0.1:8000/tests/${id}/questions`, {
headers: { Authorization: `Bearer ${token}` }
})
.then(res => res.json())
.then(data => {

setQuestions(data);

if (data.length > 0) {
setTimeLeft(data[0].time_limit);
}

})
.catch(err => console.error(err));

}, [id, token]);



// ---------------- RECORD AUDIO ----------------

const startRecording = async () => {

const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

const recorder = new MediaRecorder(stream);

let chunks = [];

recorder.ondataavailable = (e) => {
chunks.push(e.data);
};

recorder.onstop = () => {

const blob = new Blob(chunks, { type: "audio/webm" });
setAudioBlob(blob);

};

recorder.start();

setMediaRecorder(recorder);
setRecording(true);
setRecordingStartTime(Date.now());

};


// ---------------- STOP RECORDING ----------------

const stopRecording = () => {

if (mediaRecorder) {
mediaRecorder.stop();
}

setRecording(false);

};



// ---------------- UPLOAD ANSWER ----------------

const uploadAnswer = useCallback(async (showEvaluation = true) => {

if (isSubmitting || !questions.length) return;

setIsSubmitting(true);

const q = questions[current];

try {

setLoadingAI(true);

if (q.question_type === "audio") {

if (!audioBlob) {
setIsSubmitting(false);
setLoadingAI(false);
return;
}

const formData = new FormData();
formData.append("file", audioBlob, "answer.webm");

const response = await fetch(
`http://127.0.0.1:8000/tests/submit-answer/${q.id}`,
{
method: "POST",
headers: { Authorization: `Bearer ${token}` },
body: formData
}
);

if (showEvaluation) {

const result = await response.json();

Swal.fire({
icon: result.final_score >= 7 ? "success" : "info",
title: `Score: ${result.final_score}/10`,
html: `
<p><b>Fluency:</b> ${result.fluency_score}</p>
<p><b>Grammar:</b> ${result.grammar_score}</p>
<p><b>Words:</b> ${result.word_count}</p>
<p><b>Feedback:</b> ${result.feedback}</p>
`
});

}

} else {

if (!textAnswer) {
setIsSubmitting(false);
setLoadingAI(false);
return;
}

const response = await fetch(
`http://127.0.0.1:8000/tests/submit-text-answer/${q.id}`,
{
method: "POST",
headers: {
"Content-Type": "application/json",
Authorization: `Bearer ${token}`
},
body: JSON.stringify({ answer: textAnswer })
}
);

if (response.ok && showEvaluation) {

const result = await response.json();

Swal.fire({
icon: result.score >= 7 ? "success" : "info",
title: `Score: ${result.score}/10`,
text: "Answer evaluated successfully"
});

}

}

} catch (error) {

console.error("Submission error:", error);

} finally {

setLoadingAI(false);
setAudioBlob(null);
setTextAnswer("");
setIsSubmitting(false);

}

}, [audioBlob, textAnswer, questions, current, token, isSubmitting]);



// ---------------- NEXT QUESTION ----------------

const nextQuestion = useCallback(async () => {

await uploadAnswer(false);

if (current < questions.length - 1) {

const nextIndex = current + 1;

setCurrent(nextIndex);

setTimeLeft(questions[nextIndex].time_limit);

}

}, [uploadAnswer, current, questions]);



// ---------------- TIMER ----------------

useEffect(() => {

if (!questions.length) return;

const timer = setInterval(() => {

setTimeLeft(prev => {

if (prev <= 1) {

clearInterval(timer);
nextQuestion();
return 0;

}

return prev - 1;

});

}, 1000);

return () => clearInterval(timer);

}, [current, questions, nextQuestion]);



// ---------------- RECORD TIMER ----------------

useEffect(() => {

let interval;

if (recording && recordingStartTime) {

interval = setInterval(() => {

setRecordingDuration(
Math.floor((Date.now() - recordingStartTime) / 1000)
);

}, 1000);

} else {

setRecordingDuration(0);

}

return () => clearInterval(interval);

}, [recording, recordingStartTime]);



// ---------------- SUBMIT TEST ----------------

const submitTest = async () => {

await uploadAnswer();

Swal.fire({
icon: "success",
title: "Test Submitted Successfully"
});

navigate(`/report/${id}`);

};



// ---------------- LOADING ----------------

if (!questions.length) {

return (

<div className="min-h-screen flex items-center justify-center text-white">
Loading questions...
</div>

);

}

const q = questions[current];



// ---------------- UI ----------------

return (

<div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-black to-purple-900 text-white">

<motion.div
initial={{ opacity: 0, scale: 0.9 }}
animate={{ opacity: 1, scale: 1 }}
className="w-[700px]"
>

<motion.h1
initial={{ y: -40, opacity: 0 }}
animate={{ y: 0, opacity: 1 }}
className="text-4xl font-bold text-center mb-8"
>
SpeakForge AI Speaking Test
</motion.h1>

<div className="w-full bg-gray-700 h-2 rounded-full mb-8 overflow-hidden">

<motion.div
initial={{ width: 0 }}
animate={{
width: `${((current + 1) / questions.length) * 100}%`
}}
className="bg-blue-500 h-2"
/>

</div>

<div className="bg-white/10 backdrop-blur-lg p-8 rounded-xl shadow-xl">

<h2 className="text-lg mb-2">
Question {current + 1} / {questions.length}
</h2>

<p className="text-xl mb-4">
{q.question_text}
</p>

<p className="text-red-400 font-semibold mb-3">
⏱ {timeLeft}s
</p>



{/* AUDIO QUESTION */}

{q.question_type === "audio" && (

<div>

{!recording ? (

<button
onClick={startRecording}
className="bg-green-500 px-6 py-2 rounded-lg hover:bg-green-600"
>
Start Recording 🎤
</button>

) : (

<button
onClick={stopRecording}
className="bg-red-500 px-6 py-2 rounded-lg hover:bg-red-600"
>
Stop Recording
</button>

)}

{recording && (

<p className="text-green-400 mt-2">
🎤 Recording... {recordingDuration}s
</p>

)}

{audioBlob && (

<audio
controls
src={URL.createObjectURL(audioBlob)}
className="w-full mt-4"
/>

)}

</div>

)}



{/* TEXT QUESTION */}

{q.question_type === "text" && (

<textarea
value={textAnswer}
onChange={(e) => setTextAnswer(e.target.value)}
placeholder="Write your answer here..."
rows="5"
className="w-full p-3 rounded-lg text-white bg-gray-800 border border-gray-600"
/>

)}



{/* AI LOADING */}

{loadingAI && (

<div className="text-center mt-4">
🤖 AI is evaluating your answer...
</div>

)}



<div className="flex gap-4 mt-6">

{current < questions.length - 1 ? (

<button
onClick={nextQuestion}
disabled={loadingAI}
className="bg-blue-600 px-6 py-2 rounded-lg hover:bg-blue-700"
>
Next →
</button>

) : (

<button
onClick={submitTest}
disabled={loadingAI}
className="bg-purple-600 px-6 py-2 rounded-lg hover:bg-purple-700"
>
Submit Test
</button>

)}

</div>

</div>

</motion.div>

</div>

);

}

export default TestDetail;