import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { API_BASE_URL } from "../config";

export default function TestReport() {

const { testId } = useParams();
const navigate = useNavigate();

const [report, setReport] = useState(null);

const token = localStorage.getItem("token");

useEffect(() => {


const interval = setInterval(() => {

  fetch(`${API_BASE_URL}/tests/report/${testId}`, {
    headers: {
      Authorization: `Bearer ${token}`
    }
  })
  .then(res => res.json())
  .then(data => {

    setReport(data);

    if (data.overall_score > 0) {
      clearInterval(interval);
    }

  })
  .catch(err => console.error(err));

}, 3000);

return () => clearInterval(interval);


}, [testId, token]);

if (!report || report.overall_score === 0) {


return (
  <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-black via-gray-900 to-black text-white">

    <div className="text-center">

      <div className="text-5xl mb-6 animate-bounce">
        🤖
      </div>

      <h1 className="text-2xl font-semibold mb-2">
        AI is analyzing your responses...
      </h1>

      <p className="text-gray-400">
        This usually takes a few seconds.
      </p>

      <div className="mt-6 animate-pulse text-blue-400">
        Generating Report...
      </div>

    </div>

  </div>
);


}

return (


<div className="min-h-screen bg-gradient-to-br from-black via-gray-900 to-black p-10 text-white">

  <div className="max-w-3xl mx-auto bg-gray-900 p-8 rounded-xl shadow-xl">

    <h1 className="text-3xl font-bold mb-6 text-center">
      AI Test Report
    </h1>


    {/* Score Cards */}

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
        <p className="text-xl font-bold text-yellow-400">
          {report.average_fluency}
        </p>
      </div>

      <div className="bg-black p-4 rounded-lg text-center">
        <p className="text-gray-400">Grammar</p>
        <p className="text-xl font-bold text-yellow-400">
          {report.average_grammar}
        </p>
      </div>

    </div>


    {/* AI Suggestions */}

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


    {/* Per Question Feedback */}

    <h2 className="text-xl font-semibold mb-4">
      Question Feedback
    </h2>

    <div className="space-y-4 mb-8">

      {report.answers?.map((a, index) => (

        <div
          key={index}
          className="bg-black p-5 rounded-lg border border-gray-700"
        >

          <h3 className="text-lg font-semibold mb-2">
            Question {index + 1}
          </h3>

          <p className="text-gray-300 mb-3">
            {a.transcript || "No transcript available"}
          </p>

          <div className="grid grid-cols-3 gap-4 text-center mb-3">

            <div className="bg-gray-900 p-2 rounded">
              <p className="text-gray-400 text-sm">Fluency</p>
              <p className="font-bold text-blue-400">{a.fluency}</p>
            </div>

            <div className="bg-gray-900 p-2 rounded">
              <p className="text-gray-400 text-sm">Grammar</p>
              <p className="font-bold text-yellow-400">{a.grammar}</p>
            </div>

            <div className="bg-gray-900 p-2 rounded">
              <p className="text-gray-400 text-sm">Score</p>
              <p className="font-bold text-green-400">{a.score}</p>
            </div>

          </div>

          <p className="text-purple-300 text-sm">
            💡 {a.feedback}
          </p>

        </div>

      ))}

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
