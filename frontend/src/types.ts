export type Entity = {
  id: string
  entity_type: string
  label: string
  description: string
  extra_data: Record<string, string>
}

export type Overview = {
  entity_count: number
  relationship_count: number
  component_count: number
  density: number
  transaction_count: number
  anomaly_count: number
  recent_activity: Array<{ id: string; amount: number; source: string; target: string; occurred_at: string }>
  disclaimer: string
}

export type Finding = {
  transaction_id: string
  entity_ids: string[]
  amount: number
  currency: string
  score: number
  confidence: string
  explanation: string
  limitations: string
}

export type Report = {
  reference_id: string
  title: string
  selected_entities: string[]
  network_summary: { entity_count: number; relationship_count: number; component_count: number; density: number }
  anomaly_findings: Finding[]
  disclaimer: string
  created_at: string
}
