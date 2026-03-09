import { useEffect, useState } from "react";
import { getTests } from "../api";

export default function Tests() {

  const [tests, setTests] = useState([]);
  const token = localStorage.getItem("token");

  useEffect(() => {
    getTests()
      .then(data => setTests(data));

  }, [token]);

  return (
    <div className="container">

      <h1 className="page-header">
        Available Tests
      </h1>

      <div className="test-grid">

        {tests.map(test => (

          <div
            key={test.id}
            className="glass-card"
          >

            <h2 className="text-xl font-bold mb-3 text-white">
              {test.title}
            </h2>

            <p className="text-gray-300 mb-6 line-clamp-3">
              {test.description}
            </p>

            <div className="flex gap-3">
              <button
                onClick={() => window.location.href = `/test/${test.id}`}
                className="btn-primary flex-1"
              >
                Start Test
              </button>
              
              <button
                onClick={() => window.location.href = `/results/${test.id}`}
                className="btn-secondary"
              >
                My Results
              </button>
            </div>

          </div>

        ))}

      </div>

      {tests.length === 0 && (
        <div className="empty-state">
          <p>No tests available at the moment.</p>
        </div>
      )}

    </div>
  );
}