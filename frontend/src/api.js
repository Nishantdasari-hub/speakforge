import { API_BASE_URL as BASE_URL } from "./config";

export const getTests = async () => {
  const res = await fetch(`${BASE_URL}/tests/`);
  return res.json();
};

export const getDashboardStats = async (token) => {
  const res = await fetch(`${BASE_URL}/tests/me/dashboard`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!res.ok) {
    throw new Error(`HTTP error! status: ${res.status}`);
  }
  return await res.json();
};

export const getRecentAnswers = async (token) => {
  const res = await fetch(`${BASE_URL}/tests/me/answers`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!res.ok) {
    throw new Error(`HTTP error! status: ${res.status}`);
  }
  return await res.json();
};

export const loginUser = async (data) => {
  const res = await fetch(`${BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  return res.json();
};

export const registerUser = async (data) => {
  const res = await fetch(`${BASE_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  return res.json();
};


export const getTestDetail = async (id) => {
  const res = await fetch(`${BASE_URL}/tests/${id}`);
  return res.json();
};

export const getMyResults = async (token) => {
  const res = await fetch(`${BASE_URL}/tests/me/results`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  return res.json();
};

