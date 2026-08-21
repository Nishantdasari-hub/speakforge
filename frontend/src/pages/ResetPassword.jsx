import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import Swal from "sweetalert2";
import { API_BASE_URL } from "../config";

function ResetPassword() {

  const { token } = useParams();
  const navigate = useNavigate();

  const [password, setPassword] = useState("");

  const handleReset = async (e) => {
    e.preventDefault();

    try {

      const response = await fetch(`${API_BASE_URL}/auth/reset-password`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          token,
          new_password: password
        })
      });

      const data = await response.json();

      if (!response.ok) {
        Swal.fire({
          icon: "error",
          title: "Reset Failed",
          text: typeof data.detail === "string"
            ? data.detail
            : "Invalid or expired reset link"
        });
        return;
      }

      Swal.fire({
        icon: "success",
        title: "Password Updated",
        text: "You can now login with your new password"
      });

      navigate("/login");

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
        onSubmit={handleReset}
        className="bg-gray-900/80 backdrop-blur-lg border border-blue-500 p-10 rounded-2xl w-[380px] shadow-2xl"
      >

        <h2 className="text-3xl font-bold text-white text-center mb-4">
          Reset Password
        </h2>

        <p className="text-gray-400 text-center mb-6">
          Enter your new password
        </p>

        <input
          type="password"
          placeholder="New Password"
          className="w-full p-3 mb-6 rounded bg-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
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
          Reset Password
        </motion.button>

      </motion.form>

    </div>
  );
}

export default ResetPassword;