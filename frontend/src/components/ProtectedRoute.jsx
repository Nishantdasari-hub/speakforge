import { Navigate } from "react-router-dom";

export default function ProtectedRoute({ children, adminOnly = false }) {

  const token = localStorage.getItem("token");
  const role = localStorage.getItem("role");

  let expired = true;
  try {
    const encoded = token?.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    expired = !encoded || JSON.parse(atob(encoded)).exp * 1000 <= Date.now();
  } catch { expired = true; }
  if (!token || expired) {
    return <Navigate to="/login" />;
  }

  if (adminOnly && role !== "admin") {
    return <Navigate to="/dashboard" />;
  }

  return children;
}