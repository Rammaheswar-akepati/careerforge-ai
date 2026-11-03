import { useState, type FormEvent } from "react";

import { registerUser } from "../api/auth";
import { ApiError } from "../api/client";
import { useAuth } from "../auth/AuthContext";

type AuthMode = "login" | "register";

export function AuthPanel() {
  const { login } = useAuth();
  const [mode, setMode] = useState<AuthMode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage("");
    setSuccessMessage("");
    setIsSubmitting(true);

    try {
      if (mode === "register") {
        await registerUser({ email, password, full_name: fullName });
        setMode("login");
        setPassword("");
        setSuccessMessage("Your account is ready. Sign in to continue.");
      } else {
        await login({ email, password });
      }
    } catch (error) {
      setErrorMessage(
        error instanceof ApiError
          ? error.message
          : "We could not complete that request. Please try again.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  function changeMode(nextMode: AuthMode) {
    setMode(nextMode);
    setErrorMessage("");
    setSuccessMessage("");
  }

  return (
    <main className="auth-page">
      <section className="auth-layout" aria-labelledby="welcome-heading">
        <div className="brand-panel">
          <div className="brand" aria-label="CareerForge AI">
            <span className="brand-mark" aria-hidden="true">
              CF
            </span>
            <span>CareerForge AI</span>
          </div>
          <div className="brand-copy">
            <p className="eyebrow">YOUR CAREER, BUILT WITH INTENTION</p>
            <p className="brand-title">
              Make your next
              <br />
              move your best one.
            </p>
            <p>
              Bring your career preparation into focus. A clearer path starts
              with understanding where you want to go.
            </p>
          </div>
          <div className="brand-footer">
            <span className="status-dot" aria-hidden="true" />
            A thoughtful workspace for your next chapter
          </div>
        </div>

        <div className="form-panel">
          <div className="mobile-brand">
            <span className="brand-mark" aria-hidden="true">
              CF
            </span>
            <span>CareerForge AI</span>
          </div>

          <div className="auth-card">
            <div className="form-heading">
              <p className="eyebrow">
                {mode === "login" ? "WELCOME BACK" : "GET STARTED"}
              </p>
              <h1 id="welcome-heading">
                {mode === "login" ? "Sign in to your account" : "Create your account"}
              </h1>
              <p>
                {mode === "login"
                  ? "Continue building a career path that feels like yours."
                  : "Set up your space and take the first step forward."}
              </p>
            </div>

            <div className="auth-tabs" role="group" aria-label="Account access">
              <button
                type="button"
                aria-pressed={mode === "login"}
                className={mode === "login" ? "auth-tab active" : "auth-tab"}
                onClick={() => changeMode("login")}
                disabled={isSubmitting}
              >
                Sign in
              </button>
              <button
                type="button"
                aria-pressed={mode === "register"}
                className={mode === "register" ? "auth-tab active" : "auth-tab"}
                onClick={() => changeMode("register")}
                disabled={isSubmitting}
              >
                Create account
              </button>
            </div>

            {successMessage && (
              <p className="form-message success-message" role="status">
                {successMessage}
              </p>
            )}
            {errorMessage && (
              <p className="form-message error-message" role="alert">
                {errorMessage}
              </p>
            )}

            <form onSubmit={handleSubmit}>
              {mode === "register" && (
                <label className="field">
                  <span>Full name</span>
                  <input
                    autoComplete="name"
                    name="fullName"
                    type="text"
                    value={fullName}
                    onChange={(event) => setFullName(event.target.value)}
                    required
                    maxLength={255}
                    disabled={isSubmitting}
                    placeholder="Your name"
                  />
                </label>
              )}
              <label className="field">
                <span>Email address</span>
                <input
                  autoComplete="email"
                  name="email"
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  required
                  disabled={isSubmitting}
                  placeholder="you@example.com"
                />
              </label>
              <label className="field">
                <span>Password</span>
                <input
                  autoComplete={mode === "login" ? "current-password" : "new-password"}
                  name="password"
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  required
                  minLength={8}
                  maxLength={128}
                  disabled={isSubmitting}
                  placeholder="Enter your password"
                />
              </label>
              <button
                className="primary-button"
                type="submit"
                disabled={
                  isSubmitting ||
                  !email.trim() ||
                  !password ||
                  (mode === "register" && !fullName.trim())
                }
              >
                {isSubmitting
                  ? "Please wait..."
                  : mode === "login"
                    ? "Sign in"
                    : "Create account"}
                {!isSubmitting && <span aria-hidden="true">→</span>}
              </button>
            </form>

            <p className="form-footnote">
              Your account keeps your career preparation personal and secure.
            </p>
          </div>
          <p className="legal-note">CareerForge AI · Your next chapter starts here</p>
        </div>
      </section>
    </main>
  );
}
