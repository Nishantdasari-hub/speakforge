import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getTests } from "../api";

export default function UserTests() {

  const [error, setError] = useState("");
  const [tests, setTests] = useState([]);
  const navigate = useNavigate();

  const token = localStorage.getItem("token");

  useEffect(() => {

    getTests().then(setTests).catch(err => setError(err.message));

  }, [token]);

  return (

    <div className="container">

      <h1 className="page-header">
        Available Tests
      </h1>

      {error && <p role="alert">{error}</p>}
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
                onClick={() => navigate(`/test/${test.id}`)}
                className="btn-primary flex-1"
              >
                Start Test
              </button>
              
              <button
                onClick={() => navigate(`/report/${test.id}`)}
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