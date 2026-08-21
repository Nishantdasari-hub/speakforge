import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import Swal from "sweetalert2";
import { API_BASE_URL } from "../config";

export default function UserDashboardSimple() {
  const [tests, setTests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [recentAnswers, setRecentAnswers] = useState([]);

  const navigate = useNavigate();
  const token = localStorage.getItem("token");

  useEffect(() => {
    const loadData = async () => {
      try {
        console.log("Loading dashboard data...");
        
        // Simple fetch with full error handling
        const testsResponse = await fetch(`${API_BASE_URL}/tests`);
        const testsData = await testsResponse.json();
        setTests(testsData || []);
        console.log("Tests loaded:", testsData);

        if (token) {
          const statsResponse = await fetch(`${API_BASE_URL}/tests/me/dashboard`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          
          if (statsResponse.ok) {
            const statsData = await statsResponse.json();
            setStats(statsData);
            console.log("Stats loaded:", statsData);
          } else {
            console.error("Stats error:", statsResponse.status);
          }

          const answersResponse = await fetch(`${API_BASE_URL}/tests/me/answers`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          
          if (answersResponse.ok) {
            const answersData = await answersResponse.json();
            setRecentAnswers(answersData.slice(0, 5));
            console.log("Answers loaded:", answersData);
          } else {
            console.error("Answers error:", answersResponse.status);
          }
        }

      } catch (error) {
        console.error("Dashboard load error:", error);
        Swal.fire({
          icon: "error",
          title: "Error",
          text: "Failed to load dashboard data"
        });
      } finally {
        setLoading(false);
      }
    };

    if (token) {
      loadData();
    }
  }, [token]);

  // Welcome Popup
  useEffect(() => {
    const email = localStorage.getItem("userEmail");
    if (email) {
      const name = email.split("@")[0];
      Swal.fire({
        title: `Welcome ${name} 👋`,
        text: "Welcome to SpeakForge AI Speaking System",
        icon: "success",
        confirmButtonColor: "#2563eb",
        timer: 2000,
        showConfirmButton: false
      });
    }
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-black text-white">
        <h1 className="text-xl animate-pulse">
          Loading Dashboard...
        </h1>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black p-10">
      {/* Dashboard Stats */}
      {stats && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gray-900 border border-green-500 shadow-xl p-6 rounded-xl mb-10 text-white"
        >
          <h2 className="text-xl font-semibold mb-4">
            Your Performance
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
            <div className="bg-black p-4 rounded-lg">
              <p className="text-gray-400">Tests Completed</p>
              <p className="text-lg font-bold">
                {stats.tests_completed ?? 0}
              </p>
            </div>
            <div className="bg-black p-4 rounded-lg">
              <p className="text-gray-400">Average Score</p>
              <p className="text-lg font-bold">
                {stats.average_score ?? 0}
              </p>
            </div>
            <div className="bg-black p-4 rounded-lg">
              <p className="text-gray-400">Level</p>
              <p className="text-lg font-bold text-green-400">
                {stats.level ?? "Beginner"}
              </p>
            </div>
          </div>
        </motion.div>
      )}

      {/* Available Tests */}
      <motion.h1
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-3xl font-bold mb-10 text-white"
      >
        Available Tests
      </motion.h1>
      {tests.length === 0 ? (
        <div className="text-center text-gray-400 text-lg">
          No tests available
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {tests.map((test, index) => (
            <motion.div
              key={test.id}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="bg-gray-900 border border-blue-500 shadow-xl p-6 rounded-xl flex justify-between items-center hover:border-blue-400 transition"
            >
              <div>
                <h2 className="text-xl font-semibold text-white">
                  {test.title}
                </h2>
                <p className="text-gray-400 text-sm">
                  {test.description}
                </p>
              </div>
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                onClick={() => navigate(`/test/${test.id}`)}
                className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
              >
                Start Test
              </motion.button>
            </motion.div>
          ))}
        </div>
      )}
      
      {/* Recent Attempts */}
      {recentAnswers.length > 0 && (
        <div className="mt-14">
          <h2 className="text-2xl text-white font-semibold mb-6">
            Recent Attempts
          </h2>
          <div className="space-y-4">
            {recentAnswers.map((ans) => (
              <div
                key={ans.id}
                className="bg-gray-900 border border-purple-500 p-4 rounded-lg flex justify-between items-center"
              >
                <div>
                  <p className="text-gray-300">
                    Question ID: {ans.question_id}
                  </p>
                  <p className="text-gray-500 text-sm">
                    Words: {ans.word_count}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold text-green-400">
                    Score: {ans.final_score}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
