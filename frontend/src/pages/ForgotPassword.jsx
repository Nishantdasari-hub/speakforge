import { useState } from "react";
import { motion } from "framer-motion";
import Swal from "sweetalert2";
import { API_BASE_URL } from "../config";

function ForgotPassword() {

  const [email, setEmail] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {

      const response = await fetch(`${API_BASE_URL}/auth/forgot-password`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          email
        })
      });

      const data = await response.json();

      if (!response.ok) {
        Swal.fire({
          icon: "error",
          title: "Error",
          text: typeof data.detail === "string"
          ? data.detail
          : JSON.stringify(data.detail)
        });
        return;
      }

      Swal.fire({
        icon: "success",
        title: "Email Sent",
        text: "If the email exists, a reset link was sent."
      });

      setEmail("");

    } catch (error) {

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
        onSubmit={handleSubmit}
        className="bg-gray-900/80 backdrop-blur-lg border border-blue-500 p-10 rounded-2xl w-[380px] shadow-2xl"
      >

        <h2 className="text-3xl font-bold text-white text-center mb-4">
          Forgot Password
        </h2>

        <p className="text-gray-400 text-center mb-6">
          Enter your email to receive a password reset link
        </p>

        <input
          type="email"
          placeholder="Enter your email"
          className="w-full p-3 mb-6 rounded bg-gray-200 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />

        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          type="submit"
          className="w-full bg-blue-600 p-3 rounded text-white font-semibold hover:bg-blue-700 transition"
        >
          Send Reset Link
        </motion.button>

      </motion.form>

    </div>

  );
}

export default ForgotPassword;