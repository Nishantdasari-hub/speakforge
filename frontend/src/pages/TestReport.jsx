import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";

export default function TestReport() {

const { testId } = useParams();
const navigate = useNavigate();

const [report, setReport] = useState(null);

useEffect(() => {

const token = localStorage.getItem("token");

fetch(`http://127.0.0.1:8000/tests/${testId}/submit`, {
method: "POST",
headers: {
Authorization: `Bearer ${token}`
}
})
.then(res => res.json())
.then(data => setReport(data));

}, [testId]);

if (!report) {

return (

<div className="min-h-screen flex items-center justify-center bg-black text-white">
<h1 className="text-xl animate-pulse">
Generating AI Report...
</h1>
</div>
);

}

return (

<div className="min-h-screen bg-gradient-to-br from-black via-gray-900 to-black p-10 text-white">

<div className="max-w-3xl mx-auto bg-gray-900 p-8 rounded-xl shadow-xl">

<h1 className="text-3xl font-bold mb-6 text-center">
AI Test Report
</h1>

<div className="grid grid-cols-2 gap-6 mb-8">

<div className="bg-black p-4 rounded-lg text-center">
<p className="text-gray-400">Overall Score</p>
<p className="text-2xl font-bold text-green-400">
{report.overall_score}
</p>
</div>

<div className="bg-black p-4 rounded-lg text-center">
<p className="text-gray-400">Level</p>
<p className="text-2xl font-bold text-blue-400">
{report.level}
</p>
</div>

<div className="bg-black p-4 rounded-lg text-center">
<p className="text-gray-400">Fluency</p>
<p className="text-xl font-bold">
{report.average_fluency}
</p>
</div>

<div className="bg-black p-4 rounded-lg text-center">
<p className="text-gray-400">Grammar</p>
<p className="text-xl font-bold">
{report.average_grammar}
</p>
</div>

</div>

<div className="mb-8">

<h2 className="text-xl font-semibold mb-4">
AI Suggestions
</h2>

<ul className="list-disc pl-5 space-y-2 text-gray-300">

{report.suggestions?.map((s, i) => (

<li key={i}>{s}</li>
))}

</ul>

</div>

<button
onClick={() => navigate("/dashboard")}
className="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg w-full"

>

Back to Dashboard

</button>

</div>

</div>

);

}
