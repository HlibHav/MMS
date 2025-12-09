export interface DateRange { start_date: string; end_date: string }

export interface PromoContext {
  geo: string
  date_range: { start: string; end: string } | DateRange
  events: any[]
  weather?: any
  seasonality?: any
}

export interface PromoOpportunity {
  id: string
  department: string
  channel: string
  date_range?: DateRange
  estimated_potential: number
  priority: number
  rationale?: string
}

export interface PromoScenario {
  id?: string
  name: string
  description?: string
  date_range: DateRange
  departments: string[]
  channels: string[]
  discount_percentage: number
  segments?: string[]
  metadata?: Record<string, any>
}

export interface ScenarioKPI {
  scenario_id?: string
  total_sales: number
  total_margin: number
  total_ebit: number
  total_units: number
  breakdown_by_channel?: Record<string, Record<string, number>>
  breakdown_by_department?: Record<string, Record<string, number>>
  breakdown_by_segment?: Record<string, Record<string, number>>
  comparison_vs_baseline?: Record<string, number>
}

export interface ValidationReport {
  scenario_id: string
  is_valid: boolean
  issues: string[]
  fixes?: string[]
  checks_passed?: Record<string, boolean>
}

export interface CreativeBrief {
  scenario_id: string
  objectives: string[]
  messaging: string
  target_audience: string
  tone: string
  style: string
  mandatory_elements: string[]
}

export interface AssetSpec {
  asset_type: string
  copy_text: string
  layout_hints?: Record<string, any>
  dimensions?: Record<string, number>
}

export interface PostMortemReport {
  scenario_id: string
  forecast_kpi: Record<string, number>
  actual_kpi: Record<string, number>
  vs_forecast?: Record<string, number>
  insights?: string[]
  learning_points?: string[]
}

export interface AnalyzeRequest {
  month: string
  geo: string
  targets?: Record<string, any>
}
