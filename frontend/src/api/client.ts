import axios from "axios";

const api = axios.create({
  // Use relative base URL so requests proxy through vite dev server in dev mode
  // and work correctly in production (browser requests go to same origin, get proxied)
  baseURL: "/",
  withCredentials: false
});

// Auto-inject Bearer token from localStorage if available
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const auth = localStorage.getItem("canvas3t.auth");
    if (auth) {
      try {
        const { token } = JSON.parse(auth);
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
      } catch {
        // Ignore parse errors
      }
    }
  }
  return config;
});

export default api;

