import { create } from "zustand";
import { loginUser, registerUser, type User } from "../api/auth";

type Credentials = {
  username: string;
  password: string;
  email?: string;
};

type AuthState = {
  user: User | null;
  token: string | null;
  status: "idle" | "loading" | "authenticated" | "error";
  error?: string;
  initialize: () => void;
  login: (credentials: Credentials) => Promise<void>;
  register: (credentials: Credentials) => Promise<void>;
  logout: () => void;
};

const STORAGE_KEY = "canvas3t.auth";

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: null,
  status: "idle",
  error: undefined,
  initialize: () => {
    if (typeof window === "undefined") return;
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    try {
      const parsed = JSON.parse(raw) as { user: User; token: string };
      set({ user: parsed.user, token: parsed.token, status: "authenticated" });
    } catch {
      localStorage.removeItem(STORAGE_KEY);
    }
  },
  login: async ({ username, password }) => {
    set({ status: "loading", error: undefined });
    try {
      const response = await loginUser({ username, password });
      if (typeof window !== "undefined") {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(response));
      }
      set({ user: response.user, token: response.token, status: "authenticated" });
    } catch (error) {
      set({ status: "error", error: "Invalid credentials" });
      throw error;
    }
  },
  register: async ({ username, email, password }) => {
    set({ status: "loading", error: undefined });
    try {
      const user = await registerUser({ username, email, password });
      // Immediately log the user in using same credentials
      await get().login({ username, password });
      if (!get().user) {
        set({ user, status: "authenticated" });
      }
    } catch (error) {
      set({ status: "error", error: "Registration failed" });
      throw error;
    }
  },
  logout: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem(STORAGE_KEY);
    }
    set({ user: null, token: null, status: "idle", error: undefined });
  }
}));

