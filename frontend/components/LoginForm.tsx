"use client";

import { FormEvent, useState } from "react";
import { useAuth } from "./AuthContext";

export default function LoginForm() {
  const { login, isAuthenticating, authError } = useAuth();
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setLocalError(null);
    try {
      await login(identifier, password);
    } catch (error) {
      if (error instanceof Error) {
        setLocalError(error.message);
      } else {
        setLocalError("Unable to log in");
      }
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="form-group">
        <label htmlFor="identifier">Email or phone number</label>
        <input
          id="identifier"
          type="text"
          placeholder="you@example.com"
          value={identifier}
          onChange={(event) => setIdentifier(event.target.value)}
          required
          autoComplete="username"
        />
      </div>
      <div className="form-group">
        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          placeholder="••••••••"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          required
          autoComplete="current-password"
        />
      </div>
      {(localError || authError) && (
        <p className="error-text">{localError ?? authError}</p>
      )}
      <button className="primary-button" type="submit" disabled={isAuthenticating}>
        {isAuthenticating ? "Signing in…" : "Sign in"}
      </button>
    </form>
  );
}
