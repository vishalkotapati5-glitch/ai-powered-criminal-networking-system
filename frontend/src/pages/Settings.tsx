import { Database, KeyRound, ShieldCheck } from 'lucide-react'

export function Settings() {
  return <div className="page-stack">
    <div className="page-heading"><div><div className="eyebrow">PREFERENCES & SAFEGUARDS</div><h1>Workspace notes</h1><p className="muted">Security and data handling information for this local demo.</p></div></div>
    <div className="settings-grid">
      <article className="panel setting-card"><div className="setting-icon"><Database size={18} /></div><h2>Dataset</h2><p>Only deterministic, fictional seed records are loaded. The demo has no connection to real-world criminal or identity databases.</p><span className="setting-status">SYNTHETIC DATA ONLY</span></article>
      <article className="panel setting-card"><div className="setting-icon"><ShieldCheck size={18} /></div><h2>Analysis limitations</h2><p>Graph structure and transaction anomalies describe data patterns only. They are not evidence of intent, culpability, or criminal activity.</p><span className="setting-status">ANALYST REVIEW REQUIRED</span></article>
      <article className="panel setting-card"><div className="setting-icon"><KeyRound size={18} /></div><h2>Local access</h2><p>API endpoints use JWT authentication and analyst role checks. Replace demonstration credentials and development signing keys before deployment.</p><span className="setting-status">DEMO CONFIGURATION</span></article>
    </div>
    <div className="footer-note">This project is a software engineering demonstration and is not designed for operational decision-making about real people.</div>
  </div>
}
