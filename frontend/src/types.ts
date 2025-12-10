export interface DateRange { start_date: string; end_date: string }

export interface PromoMechanic {
  department: string
  channel: string
  discount_pct: number
  segments?: string[]
  notes?: string
  product_focus?: string[]
}

export interface PromoContext {
  geo: string
  date_range: { start: string; end: string } | DateRange
  events: any[]
  weather?: any
  seasonality?: any
  weekend_patterns?: Record<string, any>
}

export interface PromoOpportunity {
  id: string
  title?: string
  promo_date_range?: { start: string; end: string }
  date_range?: DateRange | null
  department?: string
  focus_departments?: string[]
  channel?: string
  estimated_potential?: {
    sales_value?: number
    margin_impact?: number
  } | number
  priority?: string | number
  rationale?: string
}

export interface PromoScenario {
  id?: string
  name?: string
  label?: string
  description?: string
  date_range: DateRange
  departments?: string[]
  channels?: string[]
  discount_percentage?: number
  mechanics?: PromoMechanic[]
  segments?: string[]
  metadata?: Record<string, any>
}

export interface ScenarioKPIBreakdown {
  channel?: string
  department?: string
  sales_value?: number
  margin_pct?: number
  margin_value?: number
  units?: number
}

export interface ScenarioKPI {
  scenario_id?: string
  period?: string
  total?: {
    sales_value?: number
    margin_value?: number
    margin_pct?: number
    ebit?: number
    units?: number
  }
  vs_baseline?: Record<string, number>
  by_channel?: ScenarioKPIBreakdown[]
  by_department?: ScenarioKPIBreakdown[]
  by_segment?: ScenarioKPIBreakdown[]
  // legacy fields for backward compatibility
  total_sales?: number
  total_margin?: number
  total_ebit?: number
  total_units?: number
  breakdown_by_channel?: Record<string, Record<string, number>>
  breakdown_by_department?: Record<string, Record<string, number>>
  breakdown_by_segment?: Record<string, Record<string, number>>
  comparison_vs_baseline?: Record<string, number>
}

export interface ValidationIssue {
  type?: string
  severity?: string
  message?: string
  suggested_fix?: string
  affected_department?: string
}

export interface ValidationReport {
  scenario_id?: string
  status?: "PASS" | "WARN" | "BLOCK"
  issues?: ValidationIssue[] | string[]
  overall_score?: number
  // legacy
  is_valid?: boolean
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
  period?: string
  forecast_kpi?: any
  actual_kpi?: any
  vs_forecast?: Record<string, number>
  post_promo_dip?: Record<string, any>
  cannibalization_signals?: Record<string, any>[]
  insights?: string[]
  learning_points?: string[]
  // legacy
  forecast_accuracy?: Record<string, number>
}

// Chat
export interface ChatMessageRequest {
  message: string
  context?: Record<string, any>
}

export interface ChatMessageResponse {
  response: string
  suggestions?: string[]
}

export interface AnalyzeRequest {
  month: string
  geo: string
  targets?: Record<string, any>
}
