import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { motion } from "framer-motion";
import Swal from "sweetalert2";

function Login() {

  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = async (e) => {
    e.preventDefault();

    try {

      const response = await fetch("http://127.0.0.1:8000/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          email,
          password
        })
      });

      const data = await response.json();

      if (!response.ok) {
        Swal.fire({
          icon: "error",
          title: "Login Failed",
          text: data.detail || "Login failed"
        });
        return;
      }

      localStorage.setItem("token", data.access_token);
      localStorage.setItem("role", data.role);
      localStorage.setItem("userEmail", email);

      if (data.role === "admin") {
        navigate("/admin/dashboard");
      } else {
        navigate("/dashboard");
      }

    } catch (error) {
      console.error("Login error:", error);
      Swal.fire({
        icon: "error",
        title: "Server Error",
        text: "Please try again later"
      });
    }
  };

  return (

    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-black via-gray-900 to-black">

      <motion.form
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        onSubmit={handleLogin}
        className="bg-gray-900/80 backdrop-blur-lg border border-blue-500 p-10 rounded-2xl w-[380px] shadow-2xl"
      >

        <h2 className="text-3xl font-bold text-white text-center mb-6">
          SpeakForge AI
        </h2>

        <p className="text-gray-400 text-center mb-6">
          AI Speaking Evaluation System
        </p>

        <input
          type="email"
          placeholder="Email"
          className="w-full p-3 mb-4 rounded bg-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />

        <input
          type="password"
          placeholder="Password"
          className="w-full p-3 mb-4 rounded bg-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          type="submit"
          className="w-full bg-blue-600 p-3 rounded text-white font-semibold hover:bg-blue-700 transition"
        >
          Login
        </motion.button>

        <p className="text-gray-400 text-center mt-5">
          Don&apos;t have an account?{" "}
          <Link to="/register" className="text-blue-400 hover:underline">
            Register
          </Link>
        </p>

      </motion.form>

    </div>

  );
}

export default Login;