
import {
  Activity,
  ArrowRight,
  ShieldCheck,
  Network,
  ScanSearch,
  FileText,
  GitFork,
  LockKeyhole,
} from 'lucide-react'

type Props = {
  onExplore: () => void
}

const features = [
  {
    icon: Network,
    title: 'Network Explorer',
    description:
      'Explore connections between fictional entities through interactive network visualizations.',
  },
  {
    icon: ScanSearch,
    title: 'Pattern Signals',
    description:
      'Identify unusual patterns and analytical signals across synthetic network data.',
  },
  {
    icon: GitFork,
    title: 'Entity Investigation',
    description:
      'Examine entity profiles, relationships and transaction histories in one workspace.',
  },
  {
    icon: FileText,
    title: 'Analytical Reports',
    description:
      'Generate structured reports and export findings for further review.',
  },
]

export function LandingPage({ onExplore }: Props) {
  return (
    <main className="landing-page">
      <nav className="landing-nav">
        <a className="landing-brand" href="#home">
          <span className="landing-brand-icon">
            <Activity size={21} />
          </span>
          <span>
            <strong>Signal Atlas</strong>
            <small>NETWORK INTELLIGENCE</small>
          </span>
        </a>

        <div className="landing-nav-links">
          <a href="#features">Features</a>
          <a href="#about">About</a>
          <button className="landing-nav-button" onClick={onExplore}>
            Sign in <ArrowRight size={15} />
          </button>
        </div>
      </nav>

      <section className="landing-hero" id="home">
        <div className="landing-hero-copy">
          <div className="landing-eyebrow">
            <span className="live-dot" />
            SIH26189 · SYNTHETIC DATA ENVIRONMENT
          </div>

          <h1>
            Intelligence,
            <span> in context.</span>
          </h1>

          <p>
            Explore complex networks, discover analytical patterns and
            investigate connections through an AI-powered synthetic network
            analysis platform.
          </p>

          <div className="landing-actions">
            <button className="landing-primary" onClick={onExplore}>
              Explore Dashboard <ArrowRight size={17} />
            </button>
            <a className="landing-secondary" href="#features">
              Discover features
            </a>
          </div>

          <div className="landing-trust">
            <ShieldCheck size={17} />
            Fictional data only · Analytical leads, never proof
          </div>
        </div>

        <div className="landing-visual" aria-label="Illustration of a connected network">
          <div className="network-orbit orbit-one" />
          <div className="network-orbit orbit-two" />
          <div className="network-center">
            <Activity size={31} />
          </div>
          <div className="network-node node-one"><Network size={18} /></div>
          <div className="network-node node-two"><ShieldCheck size={18} /></div>
          <div className="network-node node-three"><GitFork size={18} /></div>
          <div className="network-node node-four"><ScanSearch size={18} /></div>
          <div className="network-caption">
            <span className="live-dot" />
            SYNTHETIC NETWORK VISUALIZATION
          </div>
        </div>
      </section>

      <section className="landing-stats">
        <div>
          <strong>AI-powered</strong>
          <span>Analytical workflows</span>
        </div>
        <div>
          <strong>Interactive</strong>
          <span>Network exploration</span>
        </div>
        <div>
          <strong>Explainable</strong>
          <span>Pattern investigation</span>
        </div>
        <div>
          <strong>Synthetic</strong>
          <span>Demonstration data</span>
        </div>
      </section>

      <section className="landing-features" id="features">
        <div className="landing-section-heading">
          <span className="landing-eyebrow">PLATFORM CAPABILITIES</span>
          <h2>Explore the network. Understand the patterns.</h2>
          <p>
            A unified workspace for exploring synthetic entities,
            relationships and analytical findings.
          </p>
        </div>

        <div className="landing-feature-grid">
          {features.map(({ icon: Icon, title, description }) => (
            <article className="landing-feature-card" key={title}>
              <div className="landing-feature-icon">
                <Icon size={21} />
              </div>
              <h3>{title}</h3>
              <p>{description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="landing-about" id="about">
        <div className="landing-about-icon">
          <LockKeyhole size={22} />
        </div>
        <div>
          <span className="landing-eyebrow">RESPONSIBLE ANALYSIS</span>
          <h2>Built for analytical exploration</h2>
          <p>
            Signal Atlas is a demonstration platform for synthetic network
            analysis. All displayed entities, relationships and transactions
            are fictional. Analytical signals are not evidence of real-world
            criminal activity.
          </p>
        </div>
      </section>

      <footer className="landing-footer">
        <span>© 2026 Signal Atlas · SIH26189</span>
        <span>Fictional data only · Educational demonstration</span>
      </footer>
    </main>
  )
}
