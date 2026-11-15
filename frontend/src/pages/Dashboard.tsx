import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Activity, ArrowUpRight, CircleDot, GitFork, Network, Radio, ShieldAlert } from 'lucide-react'
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api } from '../services/api'
import type { Overview } from '../types'

export function Dashboard() {
  const [data, setData] = useState<Overview | null>(null)
  const [types, setTypes] = useState<Array<{ type: string; count: number }>>([])
  const [error, setError] = useState('')
  useEffect(() => {
    Promise.all([api<Overview>('/dashboard/overview'), api<{ entities_by_type: typeof types }>('/dashboard/statistics')])
      .then(([overview, stats]) => { setData(overview); setTypes(stats.entities_by_type) })
      .catch(issue => setError(issue instanceof Error ? issue.message : 'Could not load dashboard'))
  }, [])

  if (error) return <div className="error-panel">{error}</div>
  if (!data) return <div className="loading">Loading synthetic workspace…</div>

  const cards = [
    { title: 'Fictional entities', value: data.entity_count, hint: 'Across 4 entity types', icon: CircleDot, color: 'cyan' },
    { title: 'Relationships', value: data.relationship_count, hint: `${data.component_count} connected components`, icon: GitFork, color: 'blue' },
    { title: 'Transaction records', value: data.transaction_count, hint: 'Synthetic activity only', icon: Activity, color: 'purple' },
    { title: 'Pattern signals', value: data.anomaly_count, hint: 'Require analyst review', icon: ShieldAlert, color: 'amber' },
  ]
  return <div className="page-stack">
    <motion.div className="page-heading" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
      <div><div className="eyebrow">SUNDAY, NOVEMBER 15 · ANALYSIS ENVIRONMENT</div><h1>Good morning, analyst <span className="wave">✳</span></h1><p className="muted">A structured view of the fictional network dataset.</p></div>
      <div className="dataset-badge"><span className="live-dot" /> SYNTHETIC DATASET <span className="badge-sep">·</span> V1.0</div>
    </motion.div>
    <div className="disclaimer"><ShieldAlert size={16} /><span><b>Investigative leads only.</b> Statistical patterns do not establish intent or culpability.</span></div>
    <section className="stats-grid">{cards.map((item, index) => <motion.article className="stat-card" key={item.title} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.07 }}>
      <div className={`stat-icon ${item.color}`}><item.icon size={18} /></div><div className="stat-title">{item.title}</div><div className="stat-value">{item.value.toLocaleString()}</div><div className="stat-hint">{item.hint}</div>
    </motion.article>)}</section>
    <section className="dashboard-grid">
      <article className="panel chart-panel"><div className="panel-head"><div><div className="eyebrow">DATASET COMPOSITION</div><h2>Entity distribution</h2></div><span className="panel-action">By type <ArrowUpRight size={14} /></span></div>
        <div className="chart-area"><ResponsiveContainer width="100%" height="100%"><BarChart data={types} margin={{ top: 8, right: 12, left: -20, bottom: 0 }}><CartesianGrid stroke="#202b3b" vertical={false} /><XAxis dataKey="type" tick={{ fill: '#77869a', fontSize: 11 }} axisLine={false} tickLine={false} /><YAxis tick={{ fill: '#77869a', fontSize: 11 }} axisLine={false} tickLine={false} /><Tooltip cursor={{ fill: '#192432' }} contentStyle={{ background: '#101722', border: '1px solid #263446', borderRadius: 9, color: '#edf4fc' }} /><Bar dataKey="count" radius={[5, 5, 0, 0]}>{types.map((_, index) => <Cell key={index} fill={['#41d9ed', '#6588ff', '#bd8bff', '#47c9a8'][index % 4]} />)}</Bar></BarChart></ResponsiveContainer></div>
        <div className="chart-foot"><span><span className="tiny-dot cyan-dot" /> {data.entity_count} entities indexed</span><span>Network density <b>{(data.density * 100).toFixed(1)}%</b></span></div>
      </article>
      <article className="panel activity-panel"><div className="panel-head"><div><div className="eyebrow">RECENT SYNTHETIC ACTIVITY</div><h2>Latest transactions</h2></div><Radio size={17} className="muted-icon" /></div>
        {data.recent_activity.length ? <div className="activity-list">{data.recent_activity.map(row => <div className="activity-row" key={row.id}><div className="activity-icon"><ArrowUpRight size={15} /></div><div className="activity-description"><b>{row.source}</b><span>to {row.target}</span></div><div className="activity-amount">${row.amount.toLocaleString()}</div></div>)}</div> : <div className="empty-state">No synthetic activity to show.</div>}
        <div className="activity-foot"><Network size={14} /> Patterns are computed from synthetic transaction activity.</div>
      </article>
    </section>
    <div className="footer-note"><ShieldAlert size={14} /> This environment contains synthetic data only. AI outputs are exploratory signals, not proof.</div>
  </div>
}
