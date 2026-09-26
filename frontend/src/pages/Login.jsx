import { Link, useNavigate } from "react-router-dom";
import { useState } from "react";

import AuthShell from "../components/AuthShell";
import api from "../services/api";

export default function Login() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    email: "",
    password: "",
  });

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (event) => {
    const { name, value } = event.target;

    setForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      const response = await api.post("/auth/login", {
        email: form.email,
        password: form.password,
      });

      localStorage.setItem(
        "rhythm_token",
        response.data.token
      );

      localStorage.setItem(
        "rhythm_user",
        JSON.stringify(response.data.user)
      );

      navigate("/camera");
    } catch (err) {
      const message =
        err.response?.data?.message ||
        "Unable to login. Please try again.";

      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell
      title="Welcome back"
      subtitle="Sign in to continue your personalized music experience."
      footer={
        <>
          Don't have an account?{" "}
          <Link to="/register">Create account</Link>
        </>
      }
    >
      <form onSubmit={handleSubmit}>
        <input
          type="email"
          name="email"
          placeholder="Email address"
          value={form.email}
          onChange={handleChange}
          autoComplete="email"
          required
        />

        <input
          type="password"
          name="password"
          placeholder="Password"
          value={form.password}
          onChange={handleChange}
          autoComplete="current-password"
          required
        />

        {error && (
          <p className="auth-error">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={loading}
        >
          {loading ? "Signing in..." : "Sign in"}
        </button>
      </form>
    </AuthShell>
  );
}