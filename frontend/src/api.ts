import axios from "axios";

export interface PromoOpportunity {
  id: string;
  title?: string;
  promo_date_range?: { start: string; end: string };
  date_range?: { start_date: string; end_date: string } | null;
  department?: string;
  focus_departments?: string[];
  channel?: string;
  estimated_potential?: { sales_value?: number; margin_impact?: number } | number;
  priority?: string | number;
  rationale?: string;
}

export interface PromoContext {
  geo: string;
  date_range: { start_date: string; end_date: string };
  events: { name: string; date: string; type: string; impact?: string }[];
  weather?: Record<string, any>;
  seasonality?: Record<string, any>;
  weekend_patterns?: Record<string, number>;
}

export interface DiscoveryDashboard {
  month: string;
  geo: string;
  summary: {
    sales_gap: number;
    margin_gap: number;
    units_gap?: number;
    gap_percentage?: Record<string, number>;
  };
  gap_timeseries: { date: string; actual: number; target: number }[];
  heatmap: { department: string; gap_pct: number; sales_value: number }[];
  context: PromoContext;
  opportunities: PromoOpportunity[];
}

export interface ChatContext {
  screen?: string;
  active_scenarios?: string[];
  user_task?: string;
  metadata?: Record<string, any>;
}

export interface DateRange {
  start_date: string;
  end_date: string;
}

export interface PromoMechanic {
  department: string;
  channel: string;
  discount_pct: number;
  segments?: string[];
}

export interface PromoScenario {
  id?: string;
  label?: string;
  name?: string;
  description?: string;
  source_opportunity_id?: string;
  date_range: DateRange;
  mechanics?: PromoMechanic[];
  scenario_type?: string;
  objectives?: Record<string, any>;
  constraints?: Record<string, any>;
  departments?: string[];
  channels?: string[];
  discount_percentage?: number;
  segments?: string[];
}

export interface PromoBrief {
  month: string;
  // Backend expects `start`/`end` keys (not start_date/end_date)
  promo_date_range?: { start: string; end: string };
  focus_departments?: string[];
  objectives?: Record<string, any>;
  constraints?: Record<string, any>;
}

export interface ScenarioKPI {
  scenario_id: string;
  total_sales: number;
  total_margin: number;
  total_ebit: number;
  total_units: number;
  breakdown_by_channel: Record<string, Record<string, number>>;
  breakdown_by_department: Record<string, Record<string, number>>;
}

export interface ValidationReport {
  scenario_id: string;
  is_valid: boolean;
  issues: string[];
  fixes: string[];
  checks_passed: Record<string, boolean>;
  status?: "PASS" | "WARN" | "BLOCK";
  overall_score?: number;
}

export interface CreativeBrief {
  scenario_id: string;
  objectives: string[];
  messaging: string;
  target_audience: string;
  tone: string;
  style: string;
  mandatory_elements: string[];
}

export interface AssetSpec {
  asset_type: string;
  copy_text: string;
  layout_hints?: Record<string, any>;
  dimensions?: Record<string, number>;
}

export interface PostMortemReport {
  scenario_id: string;
  forecast_accuracy: Record<string, number>;
  uplift_analysis: Record<string, any>;
  post_promo_dip?: number;
  cannibalization_signals?: string[];
  insights: string[];
}

const API_ROOT = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const client = axios.create({
  baseURL: `${API_ROOT.replace(/\/$/, "")}/api/v1`,
  headers: {
    Authorization: "Bearer test", // dev default, align with backend stub
  },
});

// Dev-only wire logging to help trace network/auth issues
if (import.meta.env.DEV) {
  client.interceptors.request.use((config) => {
    console.debug("[api] request", {
      method: config.method,
      url: config.url,
      baseURL: config.baseURL,
      params: config.params,
      data: config.data,
      headers: {
        authorization: config.headers?.Authorization || config.headers?.authorization,
      },
    });
    return config;
  });

  client.interceptors.response.use(
    (response) => {
      console.debug("[api] response", {
        url: response.config.url,
        status: response.status,
        data: response.data,
      });
      return response;
    },
    (error) => {
      console.error("[api] error", {
        url: error.config?.url,
        status: error.response?.status,
        data: error.response?.data,
        message: error.message,
      });
      return Promise.reject(error);
    },
  );
}

export const fetchBaseline = async (start: string, end: string) => {
  const res = await client.get("/data/baseline", { params: { start_date: start, end_date: end } });
  return res.data;
};

export const fetchDiscoveryMonths = async (): Promise<string[]> => {
  const res = await client.get("/discovery/months");
  return res.data;
};

export const fetchDiscoveryDashboard = async (month: string, geo: string): Promise<DiscoveryDashboard> => {
  const res = await client.get("/discovery/dashboard", { params: { month, geo } });
  return res.data;
};

export const fetchOpportunities = async (month: string, geo: string) => {
  const res = await client.get("/discovery/opportunities", { params: { month, geo } });
  return res.data;
};

export const fetchGaps = async (month: string, geo: string) => {
  const res = await client.get("/discovery/gaps", { params: { month, geo } });
  return res.data;
};

export const analyzeDiscovery = async (month: string, geo: string) => {
  const res = await client.post("/discovery/analyze", null, { params: { month, geo } });
  return res.data;
};

export const fetchSegments = async () => {
  const res = await client.get("/data/segments");
  return res.data;
};

export const fetchUpliftModel = async (department?: string, channel?: string) => {
  const res = await client.get("/data/uplift-model", { params: { department, channel } });
  return res.data;
};

export const sendChatMessage = async (message: string, context?: ChatContext) => {
  const res = await client.post("/chat/message", { message, context });
  return res.data;
};

export const createScenarioFromBrief = async (brief: PromoBrief, scenario_type = "balanced", parameters?: Record<string, any>) => {
  const res = await client.post("/scenarios/create", { brief, scenario_type, parameters });
  return res.data as { scenario: PromoScenario; kpi?: any; validation?: any };
};

export const evaluateScenario = async (scenario: PromoScenario) => {
  const res = await client.post("/scenarios/evaluate", scenario);
  return res.data as ScenarioKPI;
};

export const validateScenario = async (scenario: PromoScenario) => {
  const res = await client.post("/scenarios/validate", scenario);
  return res.data as ValidationReport;
};

export const compareScenarios = async (scenarios: PromoScenario[]) => {
  const res = await client.post("/scenarios/compare", scenarios);
  return res.data;
};

export const optimizeScenarios = async (brief: string, constraints?: Record<string, any>, objectives?: Record<string, any>) => {
  const res = await client.post("/optimization/generate", { brief, constraints, objectives });
  return res.data as {
    scenarios: { scenario: PromoScenario; kpi: any; validation: any; rank: number; score: number }[];
    efficient_frontier?: { points: { sales: number; margin: number; ebit: number; scenario_id: string }[]; pareto_optimal: string[] };
  };
};

export const getFrontier = async (scenarios: PromoScenario[]) => {
  const res = await client.post("/optimization/frontier", scenarios);
  return res.data as { scenarios: PromoScenario[]; coordinates: [number, number][]; pareto_optimal: boolean[] };
};

export const generateCreativeBrief = async (scenario: PromoScenario) => {
  const res = await client.post("/creative/brief", scenario);
  return res.data as CreativeBrief;
};

export const generateCreativeAssets = async (brief: CreativeBrief) => {
  const res = await client.post("/creative/assets", brief);
  return res.data as AssetSpec[];
};

export const finalizeCampaign = async (scenarios: PromoScenario[]) => {
  const res = await client.post("/creative/finalize", scenarios);
  return res.data;
};

export const analyzePostMortem = async (scenario_id: string) => {
  const res = await client.post("/postmortem/analyze", {
    scenario_id,
    actual_data: {},
    period: { start: "2024-10-01", end: "2024-10-31" },
  });
  return res.data as PostMortemReport;
};
