import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { apiRequest } from "../api";

export default function TestReport() {
  const { testId } = useParams();
  const [params] = useSearchParams();
  const attempt = params.get("attempt");
  const [report, setReport] = useState(null);
  const [error, setError] = useState("");
  const [refresh, setRefresh] = useState(0);

  useEffect(() => {
    let active = true, timer;
    setError("");
    const poll = async () => {
      try {
        const data = await apiRequest(`/tests/report/${testId}${attempt ? `?attempt_id=${attempt}` : ""}`);
        if (!active) return;
        setReport(data);
        if (data.status === "processing") timer = setTimeout(poll, 3000);
      } catch (err) { if (active) setError(err.message); }
    };
    poll();
    return () => { active = false; clearTimeout(timer); };
  }, [testId, attempt, refresh]);

  const retry = async () => {
    try {
      await apiRequest(`/tests/attempts/${report.attempt_id}/retry`, { method:"POST" });
      setRefresh(value => value + 1);
    } catch (err) { setError(err.message); }
  };

  return <main className="min-h-screen bg-gray-950 text-white p-6">
    <section className="max-w-3xl mx-auto bg-gray-900 rounded-xl p-8 space-y-6">
      <h1 className="text-3xl font-bold">Practice Test Report</h1>
      {error && <div role="alert"><p className="text-red-300">{error}</p><button onClick={() => setRefresh(value => value + 1)}>Reload report</button></div>}
      {!error && !report && <p role="status">Loading report...</p>}
      {report?.status === "processing" && <p role="status">Your responses are queued or being evaluated. You can leave this page and return from your result history. Initial model setup can take several minutes.</p>}
      {report?.status === "draft" && <Link to={`/test/${testId}`} className="text-blue-400">Continue your unfinished attempt</Link>}
      {report?.status === "failed" && <div role="alert"><p>Some answers could not be evaluated. Your responses are saved.</p><button onClick={retry} className="bg-blue-600 p-3 rounded mt-3">Retry Evaluation</button></div>}
      {report?.status === "completed" && <>
        <h2 className="text-xl">{report.title}</h2>
        <div className="grid grid-cols-2 gap-4">
          {[['Overall Score',report.overall_score],['Practice Level',report.level],['Fluency',report.average_fluency],['Grammar',report.average_grammar]].map(([label,value]) => <div key={label} className="bg-black p-4 rounded"><p>{label}</p><p className="text-2xl">{value}</p></div>)}
        </div>
        <p className="text-gray-400">{report.scoring_note}</p>
        <h2 className="text-xl">Suggestions</h2>
        <ul className="list-disc pl-5">{report.suggestions.map(item => <li key={item}>{item}</li>)}</ul>
      </>}
      {report?.answers.map((answer,index) => <article key={answer.question_id} className="bg-black p-5 rounded space-y-2">
        <h2 className="font-bold">Question {index + 1}: {answer.question_text}</h2>
        <p>{answer.transcript || answer.written_answer || "No speech detected or transcription pending."}</p>
        <p>Score: {answer.score ?? "Pending"} · Grammar: {answer.grammar ?? "Pending"} · Fluency: {answer.fluency ?? "Pending"}</p>
        <p>{answer.feedback || answer.error || answer.status}</p>
      </article>)}
      <nav className="flex gap-6 text-blue-400"><Link to="/dashboard">Back to Dashboard</Link><Link to="/my-results">Result History</Link></nav>
    </section>
  </main>;
}
