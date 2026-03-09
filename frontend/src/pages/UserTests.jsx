import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

export default function UserTests() {

  const [tests, setTests] = useState([]);
  const navigate = useNavigate();

  const token = localStorage.getItem("token");

  useEffect(() => {

    fetch("http://127.0.0.1:8000/tests/", {
      headers: {
        Authorization: `Bearer ${token}`
      }
    })
      .then(res => res.json())
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
                onClick={() => navigate(`/test/${test.id}`)}
                className="btn-primary flex-1"
              >
                Start Test
              </button>
              
              <button
                onClick={() => navigate(`/results/${test.id}`)}
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