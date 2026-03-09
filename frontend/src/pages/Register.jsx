import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import Swal from "sweetalert2";

const BASE_URL = "http://127.0.0.1:8000";

export default function Register() {

  const navigate = useNavigate();

  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    is_admin: false,
    admin_key: ""
  });

  const [error, setError] = useState("");

  const handleChange = (e) => {

    const { name, value, type, checked } = e.target;

    setForm({
      ...form,
      [name]: type === "checkbox" ? checked : value
    });

  };

  const handleSubmit = async (e) => {

    e.preventDefault();
    setError("");

    try {

      const res = await fetch(`${BASE_URL}/auth/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(form)
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.detail || "Registration failed");
        return;
      }

      Swal.fire({
        title: "Registration Successful 🎉",
        text: "Your account has been created. Please login.",
        icon: "success",
        confirmButtonColor: "#2563eb"
      });

      navigate("/login");

    } catch (err) {

      console.error(err);
      setError("Server error");

    }

  };

  return (

    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-black via-gray-900 to-black">

      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="bg-gray-900/80 backdrop-blur-lg border border-green-500 p-10 rounded-2xl w-[420px] shadow-2xl"
      >

        <h2 className="text-3xl font-bold text-center text-white mb-2">
          Create Account
        </h2>

        <p className="text-center text-gray-400 mb-6">
          Join SpeakForge AI
        </p>


        {error && (
          <div className="bg-red-500/20 text-red-400 p-3 rounded-lg text-sm mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">

          <input
            type="text"
            name="name"
            placeholder="Full Name"
            required
            value={form.name}
            onChange={handleChange}
            className="w-full p-3 bg-gray-800 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-green-500"
          />

          <input
            type="email"
            name="email"
            placeholder="Email"
            required
            value={form.email}
            onChange={handleChange}
            className="w-full p-3 bg-gray-800 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-green-500"
          />

          <input
            type="password"
            name="password"
            placeholder="Password"
            required
            value={form.password}
            onChange={handleChange}
            className="w-full p-3 bg-gray-800 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-green-500"
          />

          {/* Admin Toggle */}

          <div className="flex items-center gap-3 mt-3">

            <input
              type="checkbox"
              name="is_admin"
              checked={form.is_admin}
              onChange={handleChange}
              className="w-4 h-4 accent-green-500"
            />

            <label className="text-gray-400 text-sm">
              Register as Admin
            </label>

          </div>


          {/* Admin Key */}

          {form.is_admin && (

            <motion.input
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              type="text"
              name="admin_key"
              placeholder="Enter Admin Secret Key"
              value={form.admin_key}
              onChange={handleChange}
              className="w-full p-3 bg-gray-800 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-green-500"
            />

          )}


          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            type="submit"
            className="w-full py-3 bg-green-600 hover:bg-green-700 rounded-lg font-semibold text-white"
          >

            Register

          </motion.button>

        </form>


        <p className="text-sm text-center text-gray-400 mt-6">

          Already have an account?{" "}

          <span
            onClick={() => navigate("/login")}
            className="text-blue-400 cursor-pointer hover:underline"
          >

            Login

          </span>

        </p>

      </motion.div>

    </div>

  );

}