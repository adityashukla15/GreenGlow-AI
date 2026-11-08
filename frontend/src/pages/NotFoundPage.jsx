import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <section className="placeholder-panel">
      <p className="eyebrow">A little off the path</p>
      <h1>We can’t find that page.</h1>
      <Link className="button button-primary" to="/">
        Return home
      </Link>
    </section>
  );
}
