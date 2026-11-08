import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import {
  Bot,
  Crown,
  Gamepad2,
  House,
  Leaf,
  Trophy,
  Users,
} from "lucide-react";
import { useUser } from "./context/UserContext.jsx";

const navigation = [
  { to: "/", label: "Home", icon: House, end: true },
  { to: "/dashboard", label: "My Green Score", icon: Leaf },
  { to: "/quiz", label: "Quiz", icon: Gamepad2 },
  { to: "/challenges", label: "Challenges", icon: Crown },
  { to: "/eco-sort", label: "Eco Sort", icon: Gamepad2 },
  { to: "/assistant", label: "AI Assistant", icon: Bot },
  { to: "/leaderboard", label: "Leaderboard", icon: Trophy },
];

export function AppLayout() {
  const { email } = useUser();
  const isLandingPage = useLocation().pathname === "/";

  return (
    <div className="app-shell">
      {!isLandingPage && (
        <header className="site-header">
          <Link className="brand" to="/" aria-label="GreenGlow home">
            <span className="brand-mark">
              <Leaf size={19} aria-hidden="true" />
            </span>
            <span>GreenGlow</span>
          </Link>
          <nav className="site-nav" aria-label="Main navigation">
            {navigation.map(({ to, label, icon: Icon, end }) => (
              <NavLink
                className={({ isActive }) =>
                  `nav-link${isActive ? " nav-link-active" : ""}`
                }
                end={end}
                key={to}
                to={to}
              >
                <Icon size={16} aria-hidden="true" />
                <span>{label}</span>
              </NavLink>
            ))}
          </nav>
          <Link className="header-profile" to="/onboarding">
            <Users size={16} aria-hidden="true" />
            <span>{email || "Choose email"}</span>
          </Link>
        </header>
      )}
      <div className={`page-content${isLandingPage ? " page-content-home" : ""}`}>
        <Outlet />
      </div>
      {!isLandingPage && (
        <footer className="site-footer">
          <span className="footer-glow" aria-hidden="true" />
          Celebrate thoughtfully. Live greener.
        </footer>
      )}
    </div>
  );
}