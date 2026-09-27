import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "https://rhythm-emotion-aware-music.onrender.com/api",
  timeout: 120000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("rhythm_token");

  config.headers = config.headers || {};
  config.headers["Content-Type"] = "application/json";

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

export default api;
