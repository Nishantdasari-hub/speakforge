import { Navigate } from "react-router-dom";

export default function ProtectedRoute({ children, adminOnly = false }) {

  const token = localStorage.getItem("token");
  const role = localStorage.getItem("role");

  if (!token) {
    return <Navigate to="/login" />;
  }

  if (adminOnly && role !== "admin") {
    return <Navigate to="/dashboard" />;
  }

  return children;
}