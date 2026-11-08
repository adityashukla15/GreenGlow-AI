import { useState } from "react";
import { motion, useReducedMotion } from "motion/react";
import {
  ArrowDown,
  ArrowRight,
  ArrowUpRight,
  Bot,
  Check,
  CircleHelp,
  Gamepad2,
  Leaf,
  Menu,
  Recycle,
  Sparkles,
  X,
} from "lucide-react";
import { Link } from "react-router-dom";

const experiences = [
  {
    number: "01",
    label: "PLAY & LEARN",
    title: "Eco Sort Game",
    description:
      "Give everyday items a second thought. Learn the basics of sorting waste.",
    icon: Recycle,
    to: "/eco-sort",
    tone: "green",
  },
  {
    number: "02",
    label: "TEST YOUR KNOW-HOW",
    title: "Green Quiz",
    description:
      "Explore sustainability ideas through a quick, friendly Diwali quiz.",
    icon: CircleHelp,
    to: "/quiz",
    tone: "gold",
  },
  {
    number: "03",
    label: "MAKE IT A HABIT",
    title: "Daily Challenges",
    description:
      "Find approachable ways to bring thoughtful choices into your festivities.",
    icon: Gamepad2,
    to: "/challenges",
    tone: "ember",
  },
  {
    number: "04",
    label: "ASK & DISCOVER",
    title: "AI Eco Assistant",
    description:
      "Get ideas for a more mindful celebration, shaped around your question.",
    icon: Bot,
    to: "/assistant",
    tone: "maroon",
  },
];

const steps = [
  {
    number: "01",
    title: "Explore",
    description: "Find games, ideas, and simple ways to celebrate with care.",
    icon: Sparkles,
  },
  {
    number: "02",
    title: "Participate",
    description: "Try a quiz, sort an item, or take on a small challenge.",
    icon: Gamepad2,
  },
  {
    number: "03",
    title: "Earn Green Points",
    description: "Completed activities add points to your GreenGlow profile.",
    icon: Check,
  },
  {
    number: "04",
    title: "Make a Difference",
    description: "Carry what you learn into choices that work for your home.",
    icon: Leaf,
  },
];

const navItems = [
  { label: "Home", href: "#home" },
  { label: "Experiences", href: "#experiences" },
  { label: "About", href: "#about" },
];

function DiyaIllustration() {
  return (
    <div className="landing-art" aria-label="Illustration of a glowing diya with leaves">
      <span className="art-halo art-halo-one" aria-hidden="true" />
      <span className="art-halo art-halo-two" aria-hidden="true" />
      <span className="art-particle art-particle-one" aria-hidden="true" />
      <span className="art-particle art-particle-two" aria-hidden="true" />
      <span className="art-particle art-particle-three" aria-hidden="true" />
      <svg
        className="diya-illustration"
        viewBox="0 0 520 520"
        role="img"
        aria-labelledby="diya-title diya-description"
      >
        <title id="diya-title">A diya for a brighter celebration</title>
        <desc id="diya-description">
          A hand-drawn golden diya surrounded by gentle green leaves and warm
          light.
        </desc>
        <defs>
          <radialGradient id="diyaGlow">
            <stop offset="0" stopColor="#F5BE70" stopOpacity=".33" />
            <stop offset="1" stopColor="#B94C32" stopOpacity="0" />
          </radialGradient>
          <linearGradient id="diyaBowl" x1="0" x2="1" y1="0" y2="1">
            <stop offset="0" stopColor="#F5BE70" />
            <stop offset=".48" stopColor="#B94C32" />
            <stop offset="1" stopColor="#6F2527" />
          </linearGradient>
          <linearGradient id="diyaFlame" x1=".2" x2=".8" y1="1" y2="0">
            <stop offset="0" stopColor="#B94C32" />
            <stop offset=".62" stopColor="#F5BE70" />
            <stop offset="1" stopColor="#FFF0D8" />
          </linearGradient>
          <linearGradient id="leafFill" x1="0" x2="1" y1="1" y2="0">
            <stop offset="0" stopColor="#426E4C" />
            <stop offset="1" stopColor="#82B98B" />
          </linearGradient>
        </defs>
        <circle cx="260" cy="248" r="205" fill="url(#diyaGlow)" />
        <ellipse
          cx="260"
          cy="420"
          rx="146"
          ry="22"
          fill="#F5BE70"
          opacity=".1"
        />
        <g fill="none" stroke="#F5BE70" strokeOpacity=".22">
          <ellipse cx="260" cy="258" rx="211" ry="127" transform="rotate(-24 260 258)" />
          <ellipse cx="260" cy="258" rx="180" ry="104" transform="rotate(28 260 258)" />
        </g>
        <g stroke="#82B98B" strokeLinecap="round" strokeWidth="3">
          <path d="M104 330c39-66 63-93 111-124" opacity=".6" />
          <path d="M416 322c-38-64-68-92-111-119" opacity=".6" />
        </g>
        <g fill="url(#leafFill)" stroke="#B4D3A5" strokeOpacity=".55">
          <path d="M133 300c-34-4-55-27-58-57 32-2 57 16 58 57Z" />
          <path d="M162 267c-6-34 9-61 36-73 10 31-2 58-36 73Z" />
          <path d="M386 296c35-4 56-27 59-57-32-2-57 16-59 57Z" />
          <path d="M357 264c6-34-9-61-36-73-10 31 2 58 36 73Z" />
        </g>
        <path
          d="M260 110c-42 45-38 86 0 113 39-27 43-68 0-113Z"
          fill="url(#diyaFlame)"
          stroke="#FFF0D8"
          strokeOpacity=".65"
          strokeWidth="2"
        />
        <path d="M260 156c-17 23-16 42 0 54 16-12 17-31 0-54Z" fill="#FFF0D8" opacity=".82" />
        <path
          d="M147 288c22 83 63 124 113 124s91-41 113-124c-61 21-165 21-226 0Z"
          fill="url(#diyaBowl)"
          stroke="#F5BE70"
          strokeWidth="3"
        />
        <path
          d="M147 288c57 20 169 20 226 0"
          fill="none"
          stroke="#FFF0D8"
          strokeOpacity=".78"
          strokeWidth="4"
        />
        <path
          d="M198 366c29 13 95 17 124 0"
          fill="none"
          stroke="#F5BE70"
          strokeOpacity=".35"
          strokeWidth="2"
        />
      </svg>
      <span className="art-caption">a little light, a little greener</span>
    </div>
  );
}

function LandingNavigation() {
  const [menuOpen, setMenuOpen] = useState(false);

  function closeMenu() {
    setMenuOpen(false);
  }

  return (
    <header className="landing-header">
      <Link className="landing-brand" to="/" aria-label="GreenGlow AI home" onClick={closeMenu}>
        <span className="landing-brand-mark">
          <Leaf size={19} aria-hidden="true" />
        </span>
        <span>GreenGlow<span className="brand-ai"> AI</span></span>
      </Link>
      <button
        className="mobile-menu-toggle"
        type="button"
        aria-label={menuOpen ? "Close navigation" : "Open navigation"}
        aria-expanded={menuOpen}
        aria-controls="landing-navigation"
        onClick={() => setMenuOpen((open) => !open)}
      >
        {menuOpen ? <X size={21} /> : <Menu size={21} />}
      </button>
      <nav
        className={`landing-navigation${menuOpen ? " landing-navigation-open" : ""}`}
        id="landing-navigation"
        aria-label="Landing page navigation"
      >
        {navItems.map((item) => (
          <a
            href={item.href}
            key={item.label}
            onClick={closeMenu}
            className="landing-nav-link"
          >
            {item.label}
          </a>
        ))}
        <Link
          className="landing-nav-cta"
          to="/onboarding"
          onClick={closeMenu}
        >
          Get Started <ArrowUpRight size={15} aria-hidden="true" />
        </Link>
      </nav>
    </header>
  );
}

export function HomePage() {
  const reducedMotion = useReducedMotion();
  const entrance = reducedMotion
    ? { initial: false, animate: { opacity: 1, y: 0 } }
    : {
        initial: { opacity: 0, y: 18 },
        animate: { opacity: 1, y: 0 },
        transition: { duration: 0.65, ease: [0.22, 1, 0.36, 1] },
      };

  return (
    <div className="landing-page" id="home">
      <LandingNavigation />
      <main>
        <section className="landing-hero landing-container">
          <motion.div className="landing-hero-copy" {...entrance}>
            <p className="landing-kicker">
              <span className="kicker-line" />
              A more mindful Diwali begins here
            </p>
            <h1>
              Celebrate
              <br />
              Brighter.
              <br />
              <span>Live Greener.</span>
            </h1>
            <p className="landing-hero-description">
              A little learning, a little play, and thoughtful ideas for a
              Diwali that feels good in every way. Find your own greener glow.
            </p>
            <div className="landing-hero-actions">
              <a className="landing-button landing-button-primary" href="#experiences">
                Explore Experiences <ArrowRight size={17} aria-hidden="true" />
              </a>
              <Link className="landing-button landing-button-secondary" to="/onboarding">
                Get Started
              </Link>
            </div>
            <p className="landing-hero-note">
              <span className="note-dot" />
              Small choices. Your own kind of celebration.
            </p>
          </motion.div>
          <motion.div
            className="landing-hero-visual"
            initial={reducedMotion ? false : { opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={
              reducedMotion
                ? { duration: 0 }
                : { duration: 0.85, delay: 0.12, ease: [0.22, 1, 0.36, 1] }
            }
          >
            <DiyaIllustration />
            <div className="visual-note visual-note-top">
              <Sparkles size={14} aria-hidden="true" />
              celebrate with care
            </div>
            <div className="visual-note visual-note-bottom">
              <Leaf size={14} aria-hidden="true" />
              keep what matters
            </div>
          </motion.div>
          <a className="hero-scroll" href="#experiences" aria-label="Scroll to experiences">
            <ArrowDown size={16} aria-hidden="true" />
          </a>
        </section>

        <motion.section
          className="landing-section experience-section"
          id="experiences"
          initial={reducedMotion ? false : { opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.16 }}
          transition={{ duration: 0.55 }}
        >
          <div className="landing-container">
            <div className="landing-section-heading">
              <div>
                <p className="landing-kicker">A little something to explore</p>
                <h2>Find your kind of green.</h2>
              </div>
              <p>
                Four ways to discover ideas and take part in a more thoughtful
                celebration.
              </p>
            </div>
            <div className="experience-grid">
              {experiences.map((experience, index) => {
                const Icon = experience.icon;
                return (
                  <motion.article
                    className={`experience-card experience-${experience.tone}`}
                    key={experience.number}
                    initial={
                      reducedMotion ? false : { opacity: 0, y: 22 }
                    }
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true, amount: 0.2 }}
                    transition={{
                      duration: 0.45,
                      delay: reducedMotion ? 0 : index * 0.09,
                    }}
                    whileHover={reducedMotion ? undefined : { y: -5 }}
                  >
                    <span className="experience-card-top">
                      <span className="experience-icon">
                        <Icon size={20} aria-hidden="true" />
                      </span>
                      <span className="experience-number">
                        {experience.number}
                      </span>
                    </span>
                    <p className="experience-label">{experience.label}</p>
                    <h3>{experience.title}</h3>
                    <p className="experience-description">
                      {experience.description}
                    </p>
                    <Link
                      className="experience-link"
                      to={experience.to}
                      aria-label={`Explore ${experience.title}`}
                    >
                      Explore <ArrowUpRight size={16} aria-hidden="true" />
                    </Link>
                    <span className="experience-preview">
                      Experience preview
                    </span>
                  </motion.article>
                );
              })}
            </div>
            <p className="experience-disclaimer">
              These experiences are being brought together for GreenGlow. Some
              are previews while the full journey takes shape.
            </p>
          </div>
        </motion.section>

        <motion.section
          className="landing-section how-section"
          id="how-it-works"
          initial={reducedMotion ? false : { opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.18 }}
          transition={{ duration: 0.55 }}
        >
          <div className="landing-container">
            <div className="landing-section-heading how-heading">
              <div>
                <p className="landing-kicker">Your journey, your pace</p>
                <h2>Four steps to a brighter Diwali.</h2>
              </div>
              <p>No perfect answers. Just curiosity and small steps forward.</p>
            </div>
            <div className="steps-grid">
              {steps.map((step, index) => {
                const Icon = step.icon;
                return (
                  <motion.div
                    className="step-card"
                    key={step.number}
                    initial={reducedMotion ? false : { opacity: 0, y: 16 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true, amount: 0.3 }}
                    transition={{
                      duration: 0.4,
                      delay: reducedMotion ? 0 : index * 0.07,
                    }}
                  >
                    <span className="step-number">{step.number}</span>
                    <span className="step-icon">
                      <Icon size={19} aria-hidden="true" />
                    </span>
                    <h3>{step.title}</h3>
                    <p>{step.description}</p>
                    {index < steps.length - 1 && (
                      <span className="step-connector" aria-hidden="true" />
                    )}
                  </motion.div>
                );
              })}
            </div>
          </div>
        </motion.section>

        <motion.section
          className="landing-section impact-section"
          id="about"
          initial={reducedMotion ? false : { opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.2 }}
          transition={{ duration: 0.55 }}
        >
          <div className="landing-container impact-layout">
            <div className="impact-art" aria-hidden="true">
              <span className="impact-ring impact-ring-one" />
              <span className="impact-ring impact-ring-two" />
              <Leaf className="impact-leaf impact-leaf-one" size={76} />
              <Leaf className="impact-leaf impact-leaf-two" size={48} />
              <Sparkles className="impact-spark impact-spark-one" size={18} />
              <Sparkles className="impact-spark impact-spark-two" size={13} />
            </div>
            <div className="impact-copy">
              <p className="landing-kicker">The meaning behind the glow</p>
              <h2>Celebrate the moments. Mind the footprint.</h2>
              <p>
                Diwali can be full of warmth without being full of waste.
                Thoughtful choices—like reusing decorations, sorting waste by
                local guidance, and choosing what you truly need—can make a
                celebration feel more intentional.
              </p>
              <p>
                GreenGlow is a place to learn and explore those ideas. Take
                what’s useful, adapt it to your home, and celebrate in a way
                that feels right for you.
              </p>
              <a className="impact-text-link" href="#how-it-works">
                See how it works <ArrowRight size={16} aria-hidden="true" />
              </a>
            </div>
          </div>
        </motion.section>

        <motion.section
          className="landing-cta landing-container"
          initial={reducedMotion ? false : { opacity: 0, y: 18 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.25 }}
          transition={{ duration: 0.5 }}
        >
          <span className="cta-flare cta-flare-one" aria-hidden="true" />
          <span className="cta-flare cta-flare-two" aria-hidden="true" />
          <div className="cta-content">
            <p className="landing-kicker">Your journey starts with a spark</p>
            <h2>Bring a little more good into the glow.</h2>
            <p>
              Choose an email to continue. It identifies your profile; it
              doesn’t sign you in or create an account.
            </p>
            <Link className="landing-button landing-button-primary" to="/onboarding">
              Start Your Green Journey <ArrowRight size={17} aria-hidden="true" />
            </Link>
          </div>
          <div className="cta-mark" aria-hidden="true">
            <Leaf size={36} />
          </div>
        </motion.section>
      </main>

      <footer className="landing-footer">
        <div className="landing-container footer-inner">
          <div className="footer-brand-block">
            <Link className="landing-brand" to="/" aria-label="GreenGlow AI home">
              <span className="landing-brand-mark">
                <Leaf size={19} aria-hidden="true" />
              </span>
              <span>GreenGlow<span className="brand-ai"> AI</span></span>
            </Link>
            <p>A brighter kind of celebration, one thoughtful choice at a time.</p>
          </div>
          <nav className="footer-links" aria-label="Footer navigation">
            <a href="#home">Home</a>
            <a href="#experiences">Experiences</a>
            <a href="#about">About</a>
            <Link to="/onboarding">Get Started</Link>
          </nav>
          <p className="footer-copyright">
            <span className="footer-glow" aria-hidden="true" />
            Celebrate thoughtfully. Live greener.
          </p>
        </div>
      </footer>
    </div>
  );
}
