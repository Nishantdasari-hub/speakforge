import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getMyResults } from "../api";

export default function MyResults() {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    getMyResults().then(setResults).catch(err => setError(err.message)).finally(() => setLoading(false));
  }, []);
  return <main className="min-h-screen bg-gray-950 text-white p-8 space-y-6">
    <Link to="/dashboard" className="text-blue-400">Back to Dashboard</Link>
    <h1 className="text-3xl font-bold">My Test Attempts</h1>
    {error && <p role="alert" className="text-red-300">{error}</p>}
    {loading ? <p>Loading Results...</p> : !results.length && !error ? <p>No test attempts yet. Complete a test to see results.</p> : results.map(result => <article key={result.attempt_id} className="bg-gray-900 border border-blue-500 rounded p-6 space-y-2">
      <h2 className="text-xl">{result.title}</h2>
      <p>Attempt #{result.attempt_id} · {new Date(result.created_at).toLocaleString()}</p>
      <p>Status: {result.status} · Score: {result.score ?? "Pending"}</p>
      <Link to={`/report/${result.test_id}?attempt=${result.attempt_id}`} className="text-blue-400">View Report</Link>
    </article>)}
  </main>;
}
