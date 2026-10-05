import { API_BASE_URL } from "./config";

export function errorMessage(data, fallback = "Request failed") {
  if (typeof data?.detail === "string") return data.detail;
  if (Array.isArray(data?.detail)) return data.detail.map(item => item.msg).join("; ");
  return fallback;
}

export async function apiRequest(path, options = {}) {
  const token = localStorage.getItem("token");
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}), ...options.headers },
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    if (response.status === 401) {
      for (const key of ["token", "role", "userEmail"]) localStorage.removeItem(key);
      window.location.assign("/login");
    }
    throw new Error(errorMessage(data, `Request failed (${response.status})`));
  }
  return data;
}

export const getTests = () => apiRequest("/tests/");
export const getDashboardStats = () => apiRequest("/tests/me/dashboard");
export const getRecentAnswers = () => apiRequest("/tests/me/answers");
export const getTestDetail = id => apiRequest(`/tests/${id}`);
export const getMyResults = () => apiRequest("/tests/me/results");
export const loginUser = data => apiRequest("/auth/login", { method: "POST", headers: {"Content-Type":"application/json"}, body:JSON.stringify(data) });
export const registerUser = data => apiRequest("/auth/register", { method: "POST", headers: {"Content-Type":"application/json"}, body:JSON.stringify(data) });
