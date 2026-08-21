import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { API_BASE_URL } from "../config";
import {
BarChart,
Bar,
XAxis,
YAxis,
Tooltip,
ResponsiveContainer,
CartesianGrid
} from "recharts";

export default function AdminAnalytics() {

const [stats, setStats] = useState({
total_tests: 0,
total_questions: 0,
total_users: 0,
total_attempts: 0
});

const token = localStorage.getItem("token");

useEffect(() => {


const fetchAnalytics = async () => {

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
    } else {
      const errorData = await res.json();
      console.error("Analytics error:", errorData);
      
      // Show specific error message
      if (res.status === 401) {
        alert("Authentication failed: Please log in as admin");
      } else if (res.status === 403) {
        alert("Access denied: Admin privileges required");
      } else {
        alert(`Error ${res.status}: ${errorData.detail || 'Unknown error'}`);
      }
    }

  } catch (error) {
    console.error("Analytics error:", error);
    alert("Network error: Could not connect to server");
  }

};

fetchAnalytics();


}, [token]);

const chartData = [
{ name: "Tests", value: stats.total_tests },
{ name: "Questions", value: stats.total_questions },
{ name: "Users", value: stats.total_users },
{ name: "Attempts", value: stats.total_attempts }
];

return (


<div className="text-white">

  <motion.h1
    initial={{ opacity: 0, y: -20 }}
    animate={{ opacity: 1, y: 0 }}
    className="text-3xl font-bold mb-10"
  >
    Analytics Dashboard
  </motion.h1>



  {/* STAT CARDS */}

  <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">

    <motion.div
      whileHover={{ scale: 1.05 }}
      className="bg-white/10 backdrop-blur-lg border border-blue-500 p-6 rounded-xl"
    >
      <p className="text-gray-400">Total Tests</p>
      <h2 className="text-4xl font-bold text-blue-400">
        {stats.total_tests}
      </h2>
    </motion.div>



    <motion.div
      whileHover={{ scale: 1.05 }}
      className="bg-white/10 backdrop-blur-lg border border-green-500 p-6 rounded-xl"
    >
      <p className="text-gray-400">Total Questions</p>
      <h2 className="text-4xl font-bold text-green-400">
        {stats.total_questions}
      </h2>
    </motion.div>



    <motion.div
      whileHover={{ scale: 1.05 }}
      className="bg-white/10 backdrop-blur-lg border border-purple-500 p-6 rounded-xl"
    >
      <p className="text-gray-400">Total Users</p>
      <h2 className="text-4xl font-bold text-purple-400">
        {stats.total_users}
      </h2>
    </motion.div>



    <motion.div
      whileHover={{ scale: 1.05 }}
      className="bg-white/10 backdrop-blur-lg border border-yellow-500 p-6 rounded-xl"
    >
      <p className="text-gray-400">Total Attempts</p>
      <h2 className="text-4xl font-bold text-yellow-400">
        {stats.total_attempts}
      </h2>
    </motion.div>

  </div>



  {/* CHART */}

  <motion.div
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    className="bg-white/10 backdrop-blur-lg border border-gray-700 p-8 rounded-xl"
  >

    <h2 className="text-xl font-semibold mb-6">
      Platform Overview
    </h2>



    <ResponsiveContainer width="100%" height={350}>

      <BarChart data={chartData}>

        <CartesianGrid strokeDasharray="3 3" stroke="#444" />

        <XAxis
          dataKey="name"
          stroke="#aaa"
        />

        <YAxis
          stroke="#aaa"
        />

        <Tooltip
          contentStyle={{
            backgroundColor: "#111",
            border: "none",
            borderRadius: "10px"
          }}
        />

        <Bar
          dataKey="value"
          fill="#3b82f6"
          radius={[6,6,0,0]}
        />

      </BarChart>

    </ResponsiveContainer>

  </motion.div>

</div>


);

}
