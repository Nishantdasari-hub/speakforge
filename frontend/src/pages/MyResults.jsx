import { useEffect, useState } from "react";
import { getMyResults } from "../api";
import { motion } from "framer-motion";

export default function MyResults() {

const [results, setResults] = useState([]);
const [loading, setLoading] = useState(true);

const token = localStorage.getItem("token");

useEffect(() => {

const loadResults = async () => {

try {

const data = await getMyResults(token);

setResults(Array.isArray(data) ? data : []);

} catch (error) {

console.error("Failed to load results:", error);

}

setLoading(false);

};

if (token) {
loadResults();
}

}, [token]);

// Loading UI
if (loading) {

return (
<div className="min-h-screen flex items-center justify-center bg-black text-white">
<h1 className="text-xl animate-pulse">
Loading Results...
</h1>
</div>
);

}

return (

<div className="min-h-screen bg-gradient-to-br from-black via-gray-900 to-purple-900 p-10 text-white">

<h1 className="text-3xl font-bold mb-10">
My Test Attempts
</h1>

{results.length === 0 ? (

<p className="text-gray-400">
No test attempts yet. Complete a test to see results.
</p>

) : (

<div className="space-y-6">

{results.map((result, index) => (

<motion.div
key={index}
initial={{ opacity: 0, y: 30 }}
animate={{ opacity: 1, y: 0 }}
className="bg-gray-900 border border-blue-500 p-6 rounded-xl shadow-lg"
>

{/* Test Info */}

<div className="mb-4">

<p className="text-lg font-semibold">
Test ID: {result.test_id}
</p>

<p className="text-gray-400">
Score: <span className="text-green-400">{result.score}</span>
</p>

<p className="text-gray-400">
Date: {result.created_at
? new Date(result.created_at).toLocaleString()
: "N/A"}
</p>

</div>

{/* Answers */}

{result.answers && result.answers.length > 0 && (

<div className="mt-4">

<h3 className="text-lg font-semibold mb-3">
Answers
</h3>

<div className="space-y-3">

{result.answers.map((ans, i) => (

<div
key={i}
className="bg-black border border-purple-500 p-4 rounded-lg"
>

<p>
Question ID: {ans.question_id}
</p>

<p className="text-gray-400">
Answer: {ans.written_answer || "Audio submitted"}
</p>

</div>

))}

</div>

</div>

)}

</motion.div>

))}

</div>

)}

</div>

);

}