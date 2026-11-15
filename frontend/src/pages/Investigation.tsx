import { useEffect, useState } from 'react'
import { ArrowDownLeft, ArrowUpRight, Clock3, Search, UserRound } from 'lucide-react'
import { api } from '../services/api'
import type { Entity } from '../types'

type TimelineEntry = { kind: string; label: string; related_entity: string | null; occurred_at: string; amount?: number }
type Profile = { entity: Entity; timeline: TimelineEntry[] }

export function Investigation() {
  const [entities, setEntities] = useState<Entity[]>([])
  const [selected, setSelected] = useState('')
  const [query, setQuery] = useState('')
  const [profile, setProfile] = useState<Profile | null>(null)
  const [error, setError] = useState('')
  useEffect(() => { api<Entity[]>('/entities').then(items => { setEntities(items); if (items[0]) setSelected(items[0].id) }).catch(issue => setError(String(issue))) }, [])
  useEffect(() => { if (selected) api<Profile>(`/entities/${selected}/activity`).then(setProfile).catch(issue => setError(String(issue))) }, [selected])
  const matches = entities.filter(entity => `${entity.id} ${entity.label}`.toLowerCase().includes(query.toLowerCase()))

  return <div className="page-stack">
    <div className="page-heading"><div><div className="eyebrow">ENTITY INVESTIGATION WORKSPACE</div><h1>Entity profile</h1><p className="muted">Review linked synthetic records and activity in chronological context.</p></div></div>
    <div className="disclaimer"><UserRound size={16} /><span>Profiles are fictional records. Connections and events are descriptive and do not imply wrongdoing.</span></div>
    <section className="explorer-layout profile-layout">
      <aside className="panel entity-list"><div className="search-box"><Search size={15} /><input placeholder="Search fictional IDs…" value={query} onChange={event => setQuery(event.target.value)} /></div><div className="entity-scroll">{matches.map(item => <button className={`entity-item ${selected === item.id ? 'selected' : ''}`} onClick={() => setSelected(item.id)} key={item.id}><span className="entity-type-dot" /><span><b>{item.label}</b><small>{item.id} · {item.entity_type}</small></span></button>)}</div></aside>
      <div className="panel profile-panel">{error ? <div className="error-panel">{error}</div> : profile ? <>
        <div className="profile-header"><div className="profile-avatar"><UserRound size={22} /></div><div><div className="eyebrow">SYNTHETIC ENTITY · {profile.entity.entity_type.toUpperCase()}</div><h2>{profile.entity.label}</h2><span>{profile.entity.id} · {profile.entity.description}</span></div></div>
        <div className="profile-section-title"><div><div className="eyebrow">RECORDED EVENTS</div><h3>Interaction timeline</h3></div><span className="panel-action"><Clock3 size={14} /> {profile.timeline.length} entries</span></div>
        {profile.timeline.length ? <div className="timeline">{profile.timeline.map((item, index) => <div className="timeline-item" key={`${item.kind}-${index}`}><div className={`timeline-icon ${item.kind}`}>{item.kind === 'transaction' ? <ArrowUpRight size={14} /> : <ArrowDownLeft size={14} />}</div><div className="timeline-body"><b>{item.label.replace(/_/g, ' ')}</b><span>{item.related_entity ? `Related entity ${item.related_entity}` : 'Synthetic location record'}</span><small>{new Date(item.occurred_at).toLocaleString()}</small></div>{item.amount !== undefined && <strong>${item.amount.toLocaleString()}</strong>}</div>)}</div> : <div className="empty-state">No activity records for this fictional entity.</div>}
      </> : <div className="loading">Loading entity profile…</div>}</div>
    </section>
  </div>
}
