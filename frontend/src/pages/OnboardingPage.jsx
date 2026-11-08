import { useState } from "react";
import { ArrowRight, Leaf, Mail, ShieldAlert } from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";
import { useUser } from "../context/UserContext.jsx";

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function OnboardingPage() {
  const { email: savedEmail, setEmail } = useUser();
  const [emailInput, setEmailInput] = useState(savedEmail);
  const [error, setError] = useState("");
  const location = useLocation();
  const navigate = useNavigate();

  function handleSubmit(event) {
    event.preventDefault();
    const normalizedEmail = emailInput.trim().toLowerCase();

    if (!EMAIL_PATTERN.test(normalizedEmail)) {
      setError("Enter a valid email address to continue.");
      return;
    }

    try {
      setEmail(normalizedEmail);
      setError("");
      navigate(location.state?.from?.pathname || "/dashboard", {
        replace: true,
      });
    } catch {
      setError(
        "Your browser could not save this email. Check your storage settings and try again.",
      );
    }
  }

  return (
    <section className="onboarding-layout">
      <div className="onboarding-panel">
        <div className="onboarding-mark">
          <Leaf size={21} aria-hidden="true" />
        </div>
        <p className="eyebrow">Your GreenGlow profile</p>
        <h1>Start with your email.</h1>
        <p className="onboarding-intro">
          Use the same email you have used with GreenGlow activities. You can
          change it any time.
        </p>

        <form className="onboarding-form" onSubmit={handleSubmit} noValidate>
          <label htmlFor="profile-email">Email address</label>
          <div className="email-field">
            <Mail size={18} aria-hidden="true" />
            <input
              autoComplete="email"
              id="profile-email"
              inputMode="email"
              name="email"
              onChange={(event) => {
                setEmailInput(event.target.value);
                setError("");
              }}
              placeholder="you@example.com"
              type="email"
              value={emailInput}
              aria-describedby={error ? "email-error" : "email-note"}
            />
          </div>
          {error && (
            <p className="form-error" id="email-error" role="alert">
              {error}
            </p>
          )}
          <p className="field-note" id="email-note">
            Your email identifies your GreenGlow profile; it does not sign you
            in or verify your identity.
          </p>
          <button className="button button-primary onboarding-submit" type="submit">
            Continue <ArrowRight size={17} aria-hidden="true" />
          </button>
        </form>

        <div className="onboarding-disclaimer">
          <ShieldAlert size={18} aria-hidden="true" />
          <p>
            This does not create an account. Some features require an existing
            backend user record; completing a quiz may create one. If a feature
            reports that your profile is not found, use the email already
            associated with your GreenGlow activity.
          </p>
        </div>
      </div>
    </section>
  );
}
