import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { FaUser, FaQuestion, FaClipboardList, FaChartLine } from "react-icons/fa";
import { API_BASE_URL } from "../config";

export default function AdminDashboard() {

  const navigate = useNavigate();

  const [stats, setStats] = useState({
    total_tests: 0,
    total_questions: 0,
    total_users: 0,
    total_attempts: 0
  });

  const token = localStorage.getItem("token");

  useEffect(() => {

    const loadStats = async () => {

      try {

        const res = await fetch(
          `${API_BASE_URL}/tests/admin/analytics`,
          {
            headers: {
              Authorization: `Bearer ${token}`
            }
          }
        );

        if (res.ok) {
          const data = await res.json();
          setStats(data);
        }

      } catch (error) {
        console.error(error);
      }

    };

    loadStats();

  }, [token]);


  return (

    <div className="min-h-screen bg-gradient-to-br from-black via-slate-900 to-black p-10 text-white">

      {/* Header */}

      <div className="flex justify-between items-center mb-10">

        <h1 className="text-4xl font-bold">
          SpeakForge Admin
        </h1>

        <p className="text-gray-400">
          AI Speaking Evaluation Platform
        </p>

      </div>


      {/* Stats */}

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">

        <StatCard
          icon={<FaClipboardList />}
          title="Total Tests"
          value={stats.total_tests}
          color="blue"
        />

        <StatCard
          icon={<FaQuestion />}
          title="Total Questions"
          value={stats.total_questions}
          color="green"
        />

        <StatCard
          icon={<FaUser />}
          title="Total Users"
          value={stats.total_users}
          color="purple"
        />

        <StatCard
          icon={<FaChartLine />}
          title="Total Attempts"
          value={stats.total_attempts}
          color="yellow"
        />

      </div>


      {/* Actions */}

      <div className="flex gap-6 mb-12">

        <ActionButton
          text="Manage Tests"
          color="blue"
          onClick={() => navigate("/admin/tests")}
        />

        <ActionButton
          text="Manage Questions"
          color="green"
          onClick={() => navigate("/admin/questions")}
        />

        <ActionButton
          text="View Analytics"
          color="purple"
          onClick={() => navigate("/admin/analytics")}
        />

      </div>


      {/* AI Analytics Placeholder */}

      <div className="bg-gray-900 border border-blue-500 rounded-xl p-8">

        <h2 className="text-2xl font-semibold mb-4">
          AI Usage Overview
        </h2>

        <p className="text-gray-400">
          This section will show AI speaking analytics like
          average score, attempts per test, and user progress.
        </p>

      </div>

    </div>

  );
}


function StatCard({ icon, title, value, color }) {

  const colors = {
    blue: "border-blue-500",
    green: "border-green-500",
    purple: "border-purple-500",
    yellow: "border-yellow-500"
  };

  return (

    <motion.div
      whileHover={{ scale: 1.05 }}
      className={`bg-gray-900 ${colors[color]} border p-6 rounded-xl shadow-xl`}
    >

      <div className="flex items-center gap-4 text-xl text-gray-300 mb-3">
        {icon}
        {title}
      </div>

      <h2 className="text-4xl font-bold">
        {value}
      </h2>

    </motion.div>

  );
}


function ActionButton({ text, color, onClick }) {

  const colors = {
    blue: "bg-blue-600 hover:bg-blue-700",
    green: "bg-green-600 hover:bg-green-700",
    purple: "bg-purple-600 hover:bg-purple-700"
  };

  return (

    <motion.button
      whileHover={{ scale: 1.1 }}
      whileTap={{ scale: 0.9 }}
      onClick={onClick}
      className={`${colors[color]} px-8 py-4 rounded-xl text-white font-semibold shadow-lg`}
    >
      {text}
    </motion.button>

  );
}