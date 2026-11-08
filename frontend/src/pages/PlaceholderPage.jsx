import { ArrowLeft, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";

export function PlaceholderPage({ title }) {
  return (
    <section className="placeholder-panel">
      <span className="placeholder-icon">
        <Sparkles size={20} aria-hidden="true" />
      </span>
      <p className="eyebrow">Coming into focus</p>
      <h1>{title}</h1>
      <p>
        This part of your GreenGlow journey is getting ready. The foundation is
        here; feature experiences will arrive in a later step.
      </p>
      <Link className="button button-quiet" to="/">
        <ArrowLeft size={16} aria-hidden="true" /> Back home
      </Link>
    </section>
  );
}
