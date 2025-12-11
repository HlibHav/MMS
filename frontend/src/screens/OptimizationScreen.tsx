import { useEffect, useMemo, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Badge, Button, Card, PanelHeader, Input, TextArea } from "react-bits";
import { Target, Sparkles, Scale, TrendingUp } from "lucide-react";
import { PromoScenario, ScenarioKPI, ValidationReport, optimizeScenarios } from "../api";
import { ScatterChart, Scatter, XAxis, YAxis, Tooltip as ReTooltip, CartesianGrid, ResponsiveContainer, Legend } from "recharts";
import { useUIStore } from "../store/uiStore";
import { formatCurrency, formatPercent, cn } from "../utils/format";

type FrontierPoint = { id: string; sales: number; margin: number; ebit: number; label: string };
type OptimizedRow = { scenario: PromoScenario; kpi?: ScenarioKPI; validation?: ValidationReport; rank?: number; score?: number };

export default function OptimizationScreen() {
  const [brief, setBrief] = useState("Optimize promotional mix");
  const [goal, setGoal] = useState<"revenue" | "margin" | "ebit">("ebit");
  const [minMargin, setMinMargin] = useState(15);
  const [maxDiscount, setMaxDiscount] = useState(25);
  const [notes, setNotes] = useState("Balance growth and profitability with guardrails.");
  const [results, setResults] = useState<OptimizedRow[]>([]);
  const scenarios = useMemo(() => results.map((r) => r.scenario), [results]);
  const [frontier, setFrontier] = useState<FrontierPoint[]>([]);
  const setChatContext = useUIStore((s) => s.setChatContext);
  const [rateLimitMessage, setRateLimitMessage] = useState<string | null>(null);
  const [cooldownUntil, setCooldownUntil] = useState<number>(0);

  const weightsForGoal = useMemo(() => {
    if (goal === "revenue") return { sales: 0.6, margin: 0.25, ebit: 0.15 };
    if (goal === "margin") return { sales: 0.25, margin: 0.6, ebit: 0.15 };
    return { sales: 0.3, margin: 0.3, ebit: 0.4 };
  }, [goal]);

  const optimizeMutation = useMutation({
    mutationFn: () =>
      optimizeScenarios(
        brief,
        { min_margin: minMargin / 100, max_discount: maxDiscount / 100, notes },
        { weights: weightsForGoal }
      ),
    onSuccess: (data) => {
      setRateLimitMessage(null);
      const optimized: OptimizedRow[] = (data.scenarios || []).map((s: any) => ({
        scenario: s.scenario,
        kpi: s.kpi,
        validation: s.validation,
        rank: s.rank,
        score: s.score,
      }));
      setResults(optimized);
      setChatContext({
        screen: "optimization",
        active_scenarios: optimized.map((s) => s.scenario.id || "").filter(Boolean),
      });
      const points = data.efficient_frontier?.points || [];
      setFrontier(
        points.map((p) => ({
          id: p.scenario_id,
          label: optimized.find((s) => s.scenario.id === p.scenario_id)?.scenario.label || p.scenario_id,
          sales: p.sales,
          margin: p.margin,
          ebit: p.ebit,
        }))
      );
    },
    onError: (err: any) => {
      if (err?.response?.status === 429) {
        setRateLimitMessage(err?.response?.data?.detail || "Rate limit reached, please wait a minute.");
        setCooldownUntil(Date.now() + 60_000);
      }
    },
  });

  // Debounced auto-generate on input changes, respecting cooldown and pending state
  useEffect(() => {
    const now = Date.now();
    if (cooldownUntil && now < cooldownUntil) return;
    if (optimizeMutation.isPending) return;
    const t = setTimeout(() => {
      optimizeMutation.mutate();
    }, 1200);
    return () => clearTimeout(t);
  }, [brief, goal, minMargin, maxDiscount, notes, weightsForGoal, optimizeMutation, cooldownUntil]);

  const recommendations = useMemo(
    () =>
      results.map((r, idx) => ({
        id: r.scenario.id || `s${idx}`,
        label: r.scenario.label || r.scenario.name || `Scenario ${idx + 1}`,
        type: r.scenario.scenario_type || "optimized",
        departments: (r.scenario.departments || []).join(", "),
        discount: `${Math.round((r.scenario.discount_percentage || 0) * 100)}%`,
        rank: r.rank,
        status: r.validation?.status || "PENDING",
        kpi: r.kpi,
        score: r.score,
        validationIssues: (r.validation?.issues || [])
          .map((i: any) => (typeof i === "string" ? i : i?.message))
          .filter(Boolean)
          .join("\n"),
      })),
    [results]
  );

  return (
    <div className="flex flex-col gap-5">
      <div className="grid gap-4 lg:grid-cols-[360px_1fr]">
        <Card className="bg-slate-950 text-slate-100 border-slate-800">
          <PanelHeader title="Objectives & constraints" eyebrow="Optimization" />
          <div className="space-y-4">
            <div className="space-y-2">
              <p className="text-xs uppercase tracking-wide text-slate-400">Optimization goal</p>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { key: "revenue", label: "Maximize Revenue", icon: TrendingUp },
                  { key: "margin", label: "Maximize Margin", icon: Scale },
                  { key: "ebit", label: "Maximize EBIT", icon: Sparkles },
                ].map((g) => {
                  const Icon = g.icon;
                  const selected = goal === g.key;
                  return (
                    <button
                      key={g.key}
                      type="button"
                      className={cn(
                        "flex flex-col items-start gap-1 rounded-xl border px-3 py-3 text-left text-sm transition",
                        selected
                          ? "border-primary-500 bg-primary-900/40 text-slate-50 ring-1 ring-primary-500"
                          : "border-slate-800 bg-slate-900 text-slate-200 hover:border-primary-500/60"
                      )}
                      onClick={() => setGoal(g.key as typeof goal)}
                    >
                      <Icon className="h-4 w-4 text-primary-300" />
                      <span>{g.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="space-y-3">
              <p className="text-xs uppercase tracking-wide text-slate-400">Hard constraints</p>
              <label className="flex flex-col gap-2 text-sm text-slate-200">
                <span className="flex items-center justify-between text-xs text-slate-400">
                  <span>Min margin floor</span>
                  <span>{minMargin}%</span>
                </span>
                <input
                  type="range"
                  min={5}
                  max={40}
                  value={minMargin}
                  onChange={(e) => setMinMargin(Number(e.target.value))}
                  className="accent-primary-500"
                />
              </label>
              <label className="flex flex-col gap-2 text-sm text-slate-200">
                <span className="flex items-center justify-between text-xs text-slate-400">
                  <span>Max discount cap</span>
                  <span>{maxDiscount}%</span>
                </span>
                <input
                  type="range"
                  min={5}
                  max={60}
                  value={maxDiscount}
                  onChange={(e) => setMaxDiscount(Number(e.target.value))}
                  className="accent-amber-400"
                />
              </label>
            </div>

            <label className="flex flex-col gap-1 text-sm text-slate-200">
              <span className="text-xs text-slate-400">Notes</span>
              <TextArea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                aria-label="Optimization notes"
                rows={3}
                className="bg-slate-900 text-slate-100"
              />
            </label>

            <Button
              className="w-full"
              onClick={() => {
                const now = Date.now();
                if (cooldownUntil && now < cooldownUntil) return;
                optimizeMutation.mutate();
              }}
              disabled={optimizeMutation.isPending}
            >
              {optimizeMutation.isPending ? "Generating..." : "Generate models"}
            </Button>
            {rateLimitMessage && <p className="text-xs text-amber-400">{rateLimitMessage}</p>}
          </div>
        </Card>

        <Card className="bg-slate-950 text-slate-100 border-slate-800">
          <PanelHeader title="Efficient frontier analysis" eyebrow="Sales vs Margin" />
          {optimizeMutation.isPending && (
            <p className="text-sm text-slate-400">Running optimization...</p>
          )}
          {frontier.length === 0 && !optimizeMutation.isPending && (
            <p className="text-sm text-slate-400">Frontier will appear after generating scenarios.</p>
          )}
          {frontier.length > 0 && (
            <div className="h-80" aria-label="Efficient frontier scatter plot">
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart>
                  <CartesianGrid stroke="#1f2937" strokeDasharray="3 3" />
                  <XAxis
                    dataKey="sales"
                    name="Sales"
                    tickFormatter={(v) => formatCurrency(v, "USD", { maximumFractionDigits: 0 })}
                    stroke="#9ca3af"
                  />
                  <YAxis
                    dataKey="margin"
                    name="Margin %"
                    tickFormatter={(v) => `${v.toFixed(1)}%`}
                    stroke="#9ca3af"
                  />
                  <ReTooltip
                    cursor={{ strokeDasharray: "3 3" }}
                    formatter={(value: any, name: any) =>
                      name === "sales" ? formatCurrency(Number(value), "USD", { maximumFractionDigits: 0 }) : `${Number(value).toFixed(1)}%`
                    }
                    labelFormatter={(label: any) => label}
                  />
                  <Legend />
                  <Scatter
                    name="Optimal"
                    data={frontier.filter((p) => (optimizeMutation.data?.efficient_frontier?.pareto_optimal || []).includes(p.id))}
                    fill="#0ea5e9"
                  />
                  <Scatter
                    name="Suboptimal"
                    data={frontier.filter((p) => !(optimizeMutation.data?.efficient_frontier?.pareto_optimal || []).includes(p.id))}
                    fill="#4b5563"
                  />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          )}
        </Card>
      </div>

      <Card className="bg-slate-950 text-slate-100 border-slate-800">
        <div className="mb-3 flex items-center justify-between">
          <PanelHeader title="AI recommendations" eyebrow={`${results.length || 0} scenarios found`} />
          {optimizeMutation.isPending && <span className="text-xs text-slate-400">Updating...</span>}
        </div>
        {results.length === 0 && <p className="text-sm text-slate-400">Generate to see recommendations.</p>}
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {recommendations.map((rec, idx) => {
            const kpi = results[idx]?.kpi;
            return (
              <div key={rec.id} className="flex flex-col gap-2 rounded-2xl border border-slate-800 bg-slate-900 p-4">
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span>#{rec.rank || idx + 1}</span>
                  <Badge tone="info" className="uppercase">
                    Score {rec.score ? Math.round(rec.score) : rec.rank ? 100 - idx * 5 : 0}
                  </Badge>
                </div>
                <p className="text-lg font-semibold text-slate-50">{rec.label}</p>
                <p className="text-xs text-slate-400">Depts: {rec.departments || "—"}</p>
                <div className="grid grid-cols-3 gap-2 text-xs text-slate-300">
                  <div className="rounded-lg border border-slate-800 bg-slate-950/70 p-2">
                    <p className="text-[10px] uppercase text-slate-500">Sales</p>
                    <p className="font-semibold">{kpi ? formatCurrency(kpi.total_sales || 0, "USD", { maximumFractionDigits: 1 }) : "–"}</p>
                  </div>
                  <div className="rounded-lg border border-slate-800 bg-slate-950/70 p-2">
                    <p className="text-[10px] uppercase text-slate-500">Margin</p>
                    <p className="font-semibold">
                      {kpi && kpi.total_sales ? formatPercent((kpi.total_margin || 0) / (kpi.total_sales || 1) * 100, { maximumFractionDigits: 1 }) : "–"}
                    </p>
                  </div>
                  <div className="rounded-lg border border-slate-800 bg-slate-950/70 p-2">
                    <p className="text-[10px] uppercase text-slate-500">EBIT</p>
                    <p className="font-semibold">{kpi ? formatCurrency(kpi.total_ebit || 0, "USD", { maximumFractionDigits: 1 }) : "–"}</p>
                  </div>
                </div>
                <p className="text-xs text-slate-400 min-h-[40px]">
                  {rec.validationIssues || "Balanced trade-off between volume and profitability."}
                </p>
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );
}
