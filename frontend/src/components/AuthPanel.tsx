import { useEffect, useState } from "react";
import { useAuthStore } from "../store/authStore";

const AuthPanel = () => {
  const { user, status, error, login, register, logout } = useAuthStore();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [form, setForm] = useState({ username: "", email: "", password: "" });

  useEffect(() => {
    useAuthStore.getState().initialize();
  }, []);

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      if (mode === "login") {
        await login({ username: form.username, password: form.password });
      } else {
        await register({
          username: form.username,
          email: form.email,
          password: form.password
        });
      }
      setForm({ username: "", email: "", password: "" });
    } catch {
      // errors handled within store
    }
  };

  if (user) {
    return (
      <div className="auth-panel">
        <span className="auth-panel__welcome">Hi, {user.username}</span>
        <button onClick={logout}>Logout</button>
      </div>
    );
  }

  return (
    <form className="auth-panel" onSubmit={handleSubmit}>
      <input
        name="username"
        placeholder="Username"
        value={form.username}
        onChange={handleChange}
        required
      />
      {mode === "register" && (
        <input
          name="email"
          placeholder="Email (optional)"
          value={form.email}
          onChange={handleChange}
        />
      )}
      <input
        type="password"
        name="password"
        placeholder="Password"
        value={form.password}
        onChange={handleChange}
        required
      />
      <div className="auth-panel__actions">
        <button type="submit" disabled={status === "loading"}>
          {mode === "login" ? "Login" : "Register"}
        </button>
        <button
          type="button"
          className="link"
          onClick={() => setMode(mode === "login" ? "register" : "login")}
        >
          {mode === "login" ? "Need an account?" : "Have an account?"}
        </button>
      </div>
      {error && <span className="auth-panel__error">{error}</span>}
    </form>
  );
};

export default AuthPanel;

