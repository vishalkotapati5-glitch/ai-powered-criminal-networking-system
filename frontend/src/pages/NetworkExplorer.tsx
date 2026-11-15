import { lazy, Suspense, useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { Background, Controls, MiniMap, ReactFlow, type Edge, type Node, type ReactFlowInstance } from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { Box, Maximize2, Search, Users, Waypoints, ZoomIn } from 'lucide-react'
import { api } from '../services/api'
import type { Entity } from '../types'
import type { ForceGraphMethods, GraphData } from 'react-force-graph-3d'

type GraphResponse = { nodes: Array<{ id: string; label: string; entity_type: string }>; edges: Array<{ source: string; target: string; type: string }> }
type GraphNode = { id: string; name: string; entity_type: string }
type GraphLink = { source: string; target: string; type: string }
const ForceGraph3D = lazy(() => import('react-force-graph-3d'))
const colors: Record<string, string> = { person: '#41d9ed', organization: '#bd8bff', phone: '#6588ff', location: '#47c9a8' }

export function NetworkExplorer() {
  const [entities, setEntities] = useState<Entity[]>([])
  const [selected, setSelected] = useState('')
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState('all')
  const [graph, setGraph] = useState<GraphResponse>({ nodes: [], edges: [] })
  const [viewMode, setViewMode] = useState<'2d' | '3d'>('2d')
  const [error, setError] = useState('')
  const [graph3DSize, setGraph3DSize] = useState({ width: 0, height: 0 })
  const graph3DRef = useRef<ForceGraphMethods | undefined>(undefined)
  const graph2DRef = useRef<ReactFlowInstance | null>(null)
  const graph3DContainerRef = useRef<HTMLDivElement | null>(null)
  const setGraph3DContainer = useCallback((container: HTMLDivElement | null) => {
    graph3DContainerRef.current = container
    if (container) setGraph3DSize({ width: container.clientWidth, height: container.clientHeight })
  }, [])

  useEffect(() => { api<Entity[]>('/entities').then(result => { setEntities(result); if (result[0]) setSelected(result[0].id) }).catch(issue => setError(String(issue))) }, [])
  useEffect(() => {
    if (!selected) return
    api<GraphResponse>(`/relationships/graph/${selected}?depth=2`).then(setGraph).catch(issue => setError(String(issue)))
  }, [selected])
  useLayoutEffect(() => {
    const container = graph3DContainerRef.current
    if (!container) return
    const resize = () => setGraph3DSize({ width: container.clientWidth, height: container.clientHeight })
    resize()
    const observer = new ResizeObserver(resize)
    observer.observe(container)
    return () => observer.disconnect()
  }, [viewMode])
  const visible = useMemo(() => entities.filter(item => (typeFilter === 'all' || item.entity_type === typeFilter) && `${item.id} ${item.label}`.toLowerCase().includes(search.toLowerCase())), [entities, typeFilter, search])
  const visibleNodes = useMemo(() => graph.nodes.filter(item => typeFilter === 'all' || item.entity_type === typeFilter), [graph.nodes, typeFilter])
  const visibleNodeIds = useMemo(() => new Set(visibleNodes.map(item => item.id)), [visibleNodes])
  const visibleEdges = useMemo(() => graph.edges.filter(edge => visibleNodeIds.has(edge.source) && visibleNodeIds.has(edge.target)), [graph.edges, visibleNodeIds])
  const nodeData: Node[] = useMemo(() => visibleNodes.map((item, index) => {
    const angle = 2 * Math.PI * index / Math.max(graph.nodes.length, 1)
    const radius = index === 0 ? 0 : 90 + index * 10
    return { id: item.id, position: { x: 360 + Math.cos(angle) * radius, y: 230 + Math.sin(angle) * radius }, data: { label: item.label, entity_type: item.entity_type }, style: { background: '#121b27', color: '#e5f2fa', border: `1px solid ${colors[item.entity_type] || '#607086'}`, borderRadius: 10, padding: '9px 12px', fontSize: 11, boxShadow: item.id === selected ? '0 0 18px #41d9ed50' : 'none' } }
  }), [graph.nodes.length, selected, visibleNodes])
  const edgeData: Edge[] = useMemo(() => visibleEdges.map((item, index) => ({ id: `${item.source}-${item.target}-${index}`, source: item.source, target: item.target, label: item.type.replace(/_/g, ' '), style: { stroke: '#34445a' }, labelStyle: { fill: '#7d8da2', fontSize: 9 }, type: 'smoothstep' })), [visibleEdges])
  const graph3DData: GraphData<GraphNode, GraphLink> = useMemo(() => ({
    nodes: visibleNodes.map((item, index) => {
      const angle = 2 * Math.PI * index / Math.max(visibleNodes.length, 1)
      const radius = 90 + index * 6
      return {
        id: item.id,
        name: item.label,
        entity_type: item.entity_type,
        x: Math.cos(angle) * radius,
        y: Math.sin(angle) * radius,
        z: ((index % 3) - 1) * 55,
      }
    }),
    links: visibleEdges.map(item => ({ source: item.source, target: item.target, type: item.type })),
  }), [visibleNodes, visibleEdges])
  useEffect(() => {
    if (viewMode !== '3d' || !graph3DData.nodes.length) return
    const timer = window.setTimeout(() => graph3DRef.current?.zoomToFit(700, 75), 1200)
    return () => window.clearTimeout(timer)
  }, [graph3DData, graph3DSize.height, graph3DSize.width, viewMode])

  return <div className="page-stack">
    <div className="page-heading"><div><div className="eyebrow">RELATIONSHIP ANALYSIS</div><h1>Network explorer</h1><p className="muted">Explore synthetic entities and their recorded connections.</p></div><span className="dataset-badge"><span className="live-dot" /> {graph.nodes.length} NODES · {graph.edges.length} EDGES</span></div>
    <div className="disclaimer"><Users size={16} /><span>Connections describe recorded synthetic associations only; they do not establish intent.</span></div>
    <section className="explorer-layout">
      <aside className="panel entity-list"><div className="search-box"><Search size={15} /><input placeholder="Search entities…" value={search} onChange={event => setSearch(event.target.value)} /></div>
        <select value={typeFilter} onChange={event => setTypeFilter(event.target.value)}><option value="all">All entity types</option><option value="person">Persons</option><option value="organization">Organizations</option><option value="phone">Phones</option><option value="location">Locations</option></select>
        <div className="entity-scroll">{visible.map(item => <button className={`entity-item ${selected === item.id ? 'selected' : ''}`} onClick={() => setSelected(item.id)} key={item.id}><span className="entity-type-dot" style={{ background: colors[item.entity_type] || '#64748b' }} /><span><b>{item.label}</b><small>{item.id} · {item.entity_type}</small></span></button>)}</div>
        {!visible.length && <div className="empty-state">No matching synthetic entities.</div>}
      </aside>
      <div className={`panel graph-panel ${viewMode === '3d' ? 'graph-panel-3d' : ''}`}>
        <div className="graph-toolbar">
          <div className="graph-mode-toggle" role="group" aria-label="Graph display mode">
            <button className={viewMode === '2d' ? 'selected' : ''} onClick={() => setViewMode('2d')}><Waypoints size={14} /> 2D</button>
            <button className={viewMode === '3d' ? 'selected' : ''} onClick={() => setViewMode('3d')}><Box size={14} /> 3D</button>
          </div>
          <button className="graph-fit" onClick={() => viewMode === '3d' ? graph3DRef.current?.zoomToFit(600, 55) : graph2DRef.current?.fitView({ duration: 500, padding: 0.18 })} title="Fit graph to view"><Maximize2 size={14} /><span>FIT</span></button>
          <span className="graph-count"><span className="live-dot" />{visibleNodes.length} nodes · {visibleEdges.length} links</span>
        </div>
        {error ? <div className="error-panel">{error}</div> : graph.nodes.length ? viewMode === '3d' ?
          <Suspense fallback={<div className="loading"><Box size={20} /> Preparing 3D scene…</div>}>
            <div className="graph-3d-canvas" ref={setGraph3DContainer}><ForceGraph3D
              ref={graph3DRef}
              width={graph3DSize.width || 800}
              height={graph3DSize.height || 500}
              graphData={graph3DData}
              backgroundColor="#0b1521"
              showNavInfo={false}
              nodeLabel={node => `${node.name} · ${node.id} · ${node.entity_type}`}
              nodeColor={node => node.id === selected ? '#f0d477' : colors[node.entity_type] || '#91a5bd'}
              nodeVal={node => node.id === selected ? 5 : 2}
              nodeResolution={16}
              linkColor={() => '#52677c'}
              linkOpacity={0.36}
              linkDirectionalParticles={1}
              linkDirectionalParticleWidth={1.5}
              linkDirectionalParticleColor={() => '#50d4e4'}
              warmupTicks={50}
              cooldownTicks={120}
              enableNodeDrag
              onNodeClick={node => { if (typeof node.id === 'string') setSelected(node.id) }}
              onEngineStop={() => graph3DRef.current?.zoomToFit(500, 55)}
            /></div>
            <div className="graph-3d-hint"><Box size={13} /> Drag to orbit · Scroll to zoom · Drag nodes to reposition</div>
          </Suspense> :
          <ReactFlow nodes={nodeData} edges={edgeData} fitView minZoom={0.25} maxZoom={2} nodesDraggable nodesConnectable={false} onInit={instance => { graph2DRef.current = instance }} onNodeClick={(_, node) => setSelected(node.id)} proOptions={{ hideAttribution: true }}><Background color="#253246" gap={24} /><Controls /><MiniMap nodeColor={node => colors[String(node.data.entity_type)] || '#41d9ed'} maskColor="#080c1470" /></ReactFlow>
          : <div className="loading"><ZoomIn size={20} /> Loading network…</div>}
      </div>
    </section>
    <div className="footer-note"><span className="tiny-dot cyan-dot" /> Drag nodes to arrange · Scroll to zoom · Connected components and communities are descriptive graph statistics.</div>
  </div>
}
