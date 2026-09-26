import { Link, useNavigate } from "react-router-dom";
import { useState } from "react";

import AuthShell from "../components/AuthShell";
import api from "../services/api";

export default function Register() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    name: "",
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
      const response = await api.post("/auth/register", {
        name: form.name,
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
        "Unable to create your account. Please try again.";

      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell
      title="Create your account"
      subtitle="Set up your RHYTHM profile for personalized music recommendations."
      footer={
        <>
          Already have an account?{" "}
          <Link to="/login">Sign in</Link>
        </>
      }
    >
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          name="name"
          placeholder="Full name"
          value={form.name}
          onChange={handleChange}
          autoComplete="name"
          required
        />

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
          autoComplete="new-password"
          minLength={8}
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
          {loading ? "Creating account..." : "Create account"}
        </button>
      </form>
    </AuthShell>
  );
}