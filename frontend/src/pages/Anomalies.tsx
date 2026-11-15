import { useEffect, useState } from 'react'
import { AlertCircle, RefreshCw, ShieldAlert, Sparkles } from 'lucide-react'
import { api } from '../services/api'
import type { Finding } from '../types'

type Results = { findings: Finding[]; method: string; limitations: string }
type Pattern = { type: string; label: string; entity_ids: string[]; explanation: string }

export function Anomalies() {
  const [results, setResults] = useState<Results | null>(null)
  const [patterns, setPatterns] = useState<Pattern[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  async function run() {
    setBusy(true); setError('')
    try { setResults(await api<Results>('/ml/anomaly-detection', { method: 'POST', body: JSON.stringify({ contamination: 0.1 }) })) }
    catch (issue) { setError(issue instanceof Error ? issue.message : 'Analysis failed') }
    finally { setBusy(false) }
  }
  useEffect(() => {
    Promise.all([api<Results>('/ml/results'), api<{ patterns: Pattern[] }>('/analysis/patterns')])
      .then(([analysis, discovery]) => { setResults(analysis); setPatterns(discovery.patterns) })
      .catch(issue => setError(String(issue)))
  }, [])

  return <div className="page-stack">
    <div className="page-heading"><div><div className="eyebrow">MACHINE-LEARNING SIGNALS</div><h1>Pattern signals</h1><p className="muted">Explore statistical outliers in fictional transaction activity.</p></div><button className="primary" onClick={run} disabled={busy}><RefreshCw size={15} className={busy ? 'spin' : ''} />{busy ? 'Analyzing…' : 'Run analysis'}</button></div>
    <div className="disclaimer"><ShieldAlert size={16} /><span><b>Not a risk score.</b> These transaction-level signals are exploratory leads only, not evidence or person-level judgments.</span></div>
    <section className="method-strip"><div className="method-icon"><Sparkles size={18} /></div><div><b>Isolation Forest + DBSCAN</b><p>Uses transaction amounts and endpoint activity counts. No sensitive personal attributes are included.</p></div><div className="method-tag">UNSUPERVISED</div></section>
    {error && <div className="error-panel">{error}</div>}
    <div className="panel findings-panel"><div className="panel-head"><div><div className="eyebrow">RESULTS</div><h2>{results?.findings.length ?? '—'} exploratory signals</h2></div><span className="panel-action">Model: {results?.method || 'Loading'}</span></div>
      {!results ? <div className="loading">Loading analysis results…</div> : results.findings.length ? <div className="findings-list">{results.findings.map(item => <article className="finding-card" key={item.transaction_id}><div className="finding-mark"><AlertCircle size={17} /></div><div className="finding-content"><div className="finding-top"><b>{item.transaction_id}</b><span className="score-pill">Outlier score {item.score.toFixed(2)}</span><strong>${item.amount.toLocaleString()} {item.currency}</strong></div><p>{item.explanation}</p><div className="finding-meta">Related fictional entities: {item.entity_ids.join(' · ')} <span>Confidence: {item.confidence}</span></div><small>{item.limitations}</small></div></article>)}</div> : <div className="empty-state roomy">No outliers in the current result. Run analysis again after refreshing the synthetic dataset.</div>}
    </div>
    <div className="panel findings-panel"><div className="panel-head"><div><div className="eyebrow">GRAPH PATTERN DISCOVERY</div><h2>{patterns.length} descriptive patterns</h2></div><span className="panel-action">Network structure · Shared records</span></div>
      {patterns.length ? <div className="findings-list">{patterns.map((pattern, index) => <article className="pattern-row" key={`${pattern.type}-${index}`}><div className="method-icon"><Sparkles size={16} /></div><div><b>{pattern.label}</b><p>{pattern.explanation}</p><small>Fictional entities: {pattern.entity_ids.join(' · ')}</small></div></article>)}</div> : <div className="empty-state">No repeated shared-record patterns detected in the current synthetic data.</div>}
    </div>
    <div className="footer-note"><ShieldAlert size={14} /> Model outputs depend on this small, synthetic sample and must be independently reviewed. A missing signal does not establish that activity is ordinary.</div>
  </div>
}
