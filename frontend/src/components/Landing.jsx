import { useNavigate } from 'react-router-dom'

export default function Landing() {
  const navigate = useNavigate()

  const handleGetStarted = () => {
    navigate('/login')
  }

  return (
    <div className="hero-shell">
      <header className="hero-nav">
        <div className="hero-logo">
          <span className="hero-logo-mark" aria-hidden="true" />
          <span className="hero-logo-text">ismap</span>
        </div>
        <button
          type="button"
          className="hero-nav-cta"
          onClick={handleGetStarted}
        >
          Get Started
        </button>
      </header>

      <main className="hero-main">
        <section className="hero-copy">
          <div className="hero-pill">Attack surface mapping</div>
          <h1 className="hero-title">
            Cyber defense that sees
            <br />
            every exposed asset.
          </h1>
          <p className="hero-body">
            ISMAP continuously discovers domains and subdomains, fingerprints services,
            and surfaces vulnerabilities &mdash; so your security team always has a live
            map of your internet-facing footprint.
          </p>
          <div className="hero-meta">
            <div className="hero-metric">
              <span className="hero-metric-label">Domains watched</span>
              <span className="hero-metric-value">1,600+</span>
            </div>
            <div className="hero-metric">
              <span className="hero-metric-label">Checks per day</span>
              <span className="hero-metric-value">100k+</span>
            </div>
            <div className="hero-metric">
              <span className="hero-metric-label">Stack coverage</span>
              <span className="hero-metric-value">300+ techs</span>
            </div>
          </div>
        </section>

        <section className="hero-auth hero-auth-placeholder">
          <div className="card hero-highlight-card">
            <p className="hero-highlight-eyebrow">Why ISMAP</p>
            <h2 className="hero-highlight-title">A living map of your internet surface.</h2>
            <ul className="hero-highlight-list">
              <li>Register your primary domains in minutes.</li>
              <li>Continuously discover subdomains and fingerprint services.</li>
              <li>Surface misconfigurations and exposed assets before attackers do.</li>
            </ul>
            <button
              type="button"
              className="hero-highlight-cta"
              onClick={handleGetStarted}
            >
              Start mapping now
            </button>
          </div>
        </section>
      </main>

      <style>{`
        .hero-shell {
          min-height: 100vh;
          display: flex;
          flex-direction: column;
          padding: 1.5rem 2rem 2.5rem;
          background: radial-gradient(circle at top left, #0f172a 0, #020617 45%, #000000 100%);
          position: relative;
          overflow: hidden;
        }
        .hero-shell::before {
          content: '';
          position: absolute;
          width: 480px;
          height: 480px;
          top: -120px;
          right: -120px;
          background: radial-gradient(circle, rgba(34, 197, 94, 0.4), transparent 70%);
          filter: blur(4px);
          opacity: 0.9;
          pointer-events: none;
        }
        .hero-shell::after {
          content: '';
          position: absolute;
          width: 380px;
          height: 380px;
          bottom: -160px;
          left: -80px;
          background: radial-gradient(circle, rgba(22, 163, 74, 0.35), transparent 70%);
          filter: blur(6px);
          opacity: 0.8;
          pointer-events: none;
        }
        .hero-nav {
          position: relative;
          z-index: 1;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding-bottom: 1rem;
        }
        .hero-logo {
          display: flex;
          align-items: center;
          gap: 0.6rem;
        }
        .hero-logo-mark {
          width: 28px;
          height: 28px;
          border-radius: 999px;
          background:
            radial-gradient(circle at 30% 30%, #bbf7d0 0, #4ade80 35%, #166534 70%, #022c22 100%);
          box-shadow:
            0 0 30px rgba(34, 197, 94, 0.75),
            0 0 80px rgba(22, 163, 74, 0.9);
        }
        .hero-logo-text {
          font-size: 1.2rem;
          font-weight: 600;
          letter-spacing: 0.16em;
          text-transform: uppercase;
        }
        .hero-nav-cta {
          padding: 0.65rem 1.4rem;
          border-radius: 999px;
          border: none;
          background: linear-gradient(90deg, #22c55e, #4ade80);
          color: #020617;
          font-weight: 600;
          box-shadow: 0 0 24px rgba(34, 197, 94, 0.5);
        }
        .hero-main {
          position: relative;
          z-index: 1;
          flex: 1;
          display: grid;
          grid-template-columns: minmax(0, 3fr) minmax(0, 2.6fr);
          gap: 2.5rem;
          align-items: center;
          padding-top: 1rem;
        }
        .hero-copy {
          max-width: 560px;
        }
        .hero-pill {
          display: inline-flex;
          align-items: center;
          gap: 0.4rem;
          padding: 0.15rem 0.7rem;
          border-radius: 999px;
          border: 1px solid rgba(74, 222, 128, 0.6);
          background: rgba(15, 23, 42, 0.7);
          font-size: 0.8rem;
          text-transform: uppercase;
          letter-spacing: 0.16em;
          color: #bbf7d0;
          margin-bottom: 1rem;
        }
        .hero-title {
          margin: 0 0 1rem;
          font-size: clamp(2.5rem, 4vw, 3.25rem);
          line-height: 1.1;
          letter-spacing: -0.03em;
        }
        .hero-body {
          margin: 0 0 1.75rem;
          color: var(--text-muted);
          max-width: 34rem;
        }
        .hero-meta {
          display: flex;
          flex-wrap: wrap;
          gap: 1.25rem 2rem;
        }
        .hero-metric-label {
          display: block;
          font-size: 0.8rem;
          text-transform: uppercase;
          letter-spacing: 0.16em;
          color: var(--text-muted);
          margin-bottom: 0.25rem;
        }
        .hero-metric-value {
          font-size: 1.15rem;
          font-weight: 600;
        }
        .hero-auth {
          justify-self: flex-end;
          max-width: 420px;
          width: 100%;
        }
        .hero-auth-placeholder .hero-highlight-card {
          position: relative;
          overflow: hidden;
        }
        .hero-highlight-card::before {
          content: '';
          position: absolute;
          inset: -1px;
          background: radial-gradient(circle at top, rgba(74, 222, 128, 0.35), transparent 55%);
          opacity: 0.8;
          mix-blend-mode: screen;
          pointer-events: none;
        }
        .hero-highlight-card > * {
          position: relative;
          z-index: 1;
        }
        .hero-highlight-eyebrow {
          margin: 0 0 0.4rem;
          font-size: 0.8rem;
          text-transform: uppercase;
          letter-spacing: 0.16em;
          color: #a3e635;
        }
        .hero-highlight-title {
          margin: 0 0 0.75rem;
          font-size: 1.3rem;
        }
        .hero-highlight-list {
          margin: 0 0 1.25rem;
          padding-left: 1.1rem;
          font-size: 0.9rem;
          color: var(--text-muted);
        }
        .hero-highlight-cta {
          width: 100%;
          padding: 0.75rem;
          border-radius: 999px;
          background: linear-gradient(90deg, #22c55e, #4ade80);
          color: #020617;
          font-weight: 600;
        }
        @media (max-width: 900px) {
          .hero-shell {
            padding: 1.25rem 1.25rem 2rem;
          }
          .hero-main {
            grid-template-columns: minmax(0, 1fr);
            gap: 2rem;
          }
          .hero-auth {
            justify-self: stretch;
            max-width: 100%;
          }
        }
        @media (max-width: 640px) {
          .hero-nav {
            gap: 0.75rem;
          }
          .hero-nav-cta {
            padding-inline: 1rem;
          }
          .hero-title {
            font-size: 2.15rem;
          }
        }
      `}</style>
    </div>
  )
}
