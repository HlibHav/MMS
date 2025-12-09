import { useMemo, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Badge, Button, Card, PanelHeader, Input, TextArea } from "react-bits";
import { PromoScenario, optimizeScenarios, getFrontier } from "../api";
import { ScatterChart, Scatter, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from "recharts";
import { useUIStore } from "../store/uiStore";

type FrontierPoint = { id: string; sales: number; margin: number; ebit: number; label: string };

export default function OptimizationScreen() {
  const [brief, setBrief] = useState("Optimize October promo mix");
  const [minMargin, setMinMargin] = useState(18);
  const [maxDiscount, setMaxDiscount] = useState(25);
  const [notes, setNotes] = useState("Balance sales uplift vs EBIT guardrails.");
  const [scenarios, setScenarios] = useState<PromoScenario[]>([]);
  const [frontier, setFrontier] = useState<FrontierPoint[]>([]);
  const setChatContext = useUIStore((s) => s.setChatContext);

  const optimizeMutation = useMutation({
    mutationFn: () => optimizeScenarios(brief, { min_margin: minMargin / 100, max_discount: maxDiscount / 100 }),
    onSuccess: (data) => {
      setScenarios(data);
      setChatContext({ screen: "optimization", active_scenarios: data.map((s) => s.id || "").filter(Boolean) });
    },
  });

  const frontierMutation = useMutation({
    mutationFn: () => getFrontier(scenarios),
    onSuccess: (data) => {
      const points = (data.coordinates || []).map((coord: [number, number], idx: number) => ({
        id: data.scenarios?.[idx]?.id || `s${idx + 1}`,
        label: data.scenarios?.[idx]?.label || data.scenarios?.[idx]?.name || `Scenario ${idx + 1}`,
        sales: coord[0],
        margin: coord[1],
        ebit: (data.scenarios?.[idx]?.constraints as any)?.ebit || 0,
      }));
      setFrontier(points);
    },
  });

  const recommendations = useMemo(
    () =>
      scenarios.map((s, idx) => ({
        id: s.id || `s${idx}`,
        label: s.label || s.name || `Scenario ${idx + 1}`,
        type: s.scenario_type || "optimized",
        departments: (s.departments || []).join(", "),
        discount: `${Math.round((s.discount_percentage || 0) * 100)}%`,
      })),
    [scenarios]
  );

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <PanelHeader title="Objectives & constraints" eyebrow="Optimization" />
        <div className="grid gap-3 md:grid-cols-3">
          <label className="flex flex-col gap-1 text-sm text-slate-700">
            <span className="text-xs text-muted">Brief</span>
            <Input value={brief} onChange={(e) => setBrief(e.target.value)} aria-label="Optimization brief" />
          </label>
          <label className="flex flex-col gap-1 text-sm text-slate-700">
            <span className="text-xs text-muted">Min margin %</span>
            <Input type="number" value={minMargin} onChange={(e) => setMinMargin(Number(e.target.value))} aria-label="Min margin percent" />
          </label>
          <label className="flex flex-col gap-1 text-sm text-slate-700">
            <span className="text-xs text-muted">Max discount %</span>
            <Input type="number" value={maxDiscount} onChange={(e) => setMaxDiscount(Number(e.target.value))} aria-label="Max discount percent" />
          </label>
          <label className="flex flex-col gap-1 text-sm text-slate-700 md:col-span-3">
            <span className="text-xs text-muted">Notes</span>
            <TextArea value={notes} onChange={(e) => setNotes(e.target.value)} aria-label="Optimization notes" rows={3} />
          </label>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          <Button onClick={() => optimizeMutation.mutate()} disabled={optimizeMutation.isPending}>
            {optimizeMutation.isPending ? "Generating..." : "Generate"}
          </Button>
          <Button variant="ghost" onClick={() => frontierMutation.mutate()} disabled={frontierMutation.isPending || scenarios.length === 0}>
            {frontierMutation.isPending ? "Calculating..." : "Frontier"}
          </Button>
        </div>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <PanelHeader title="Recommended scenarios" eyebrow="Ranked" />
          {scenarios.length === 0 && <p className="text-sm text-muted">No scenarios yet. Generate to see recommendations.</p>}
          <ul className="divide-y divide-border/60">
            {recommendations.map((rec) => (
              <li key={rec.id} className="flex items-center justify-between py-3">
                <div>
                  <p className="font-semibold text-slate-900">{rec.label}</p>
                  <p className="text-xs text-muted">{rec.type}</p>
                  <p className="text-xs text-muted">Depts: {rec.departments || "—"}</p>
                </div>
                <Badge tone="success">Disc {rec.discount}</Badge>
              </li>
            ))}
          </ul>
        </Card>

        <Card>
          <PanelHeader title="Efficient frontier" eyebrow="Sales vs Margin" />
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart>
                <CartesianGrid />
                <XAxis dataKey="sales" name="Sales" />
                <YAxis dataKey="margin" name="Margin" />
                <Tooltip cursor={{ strokeDasharray: "3 3" }} />
                <Scatter data={frontier} fill="#0ea5e9">
                  {frontier.map((p) => (
                    <text key={p.id} x={p.sales} y={p.margin} dy={-6} fontSize={10} textAnchor="middle">
                      {p.label}
                    </text>
                  ))}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      <Card>
        <PanelHeader title="Constraint summary" eyebrow="Guards & notes" />
        <div className="grid gap-3 md:grid-cols-3 text-sm text-slate-800">
          <div className="rounded-xl border border-border bg-surface-50 p-3">
            <p className="text-xs uppercase tracking-wide text-muted">Brief</p>
            <p className="font-semibold text-slate-900">{brief}</p>
          </div>
          <div className="rounded-xl border border-border bg-surface-50 p-3">
            <p className="text-xs uppercase tracking-wide text-muted">Min margin</p>
            <p className="font-semibold text-slate-900">{minMargin}%</p>
          </div>
          <div className="rounded-xl border border-border bg-surface-50 p-3">
            <p className="text-xs uppercase tracking-wide text-muted">Max discount</p>
            <p className="font-semibold text-slate-900">{maxDiscount}%</p>
          </div>
        </div>
        <p className="mt-3 text-sm text-slate-700">{notes}</p>
      </Card>
    </div>
  );
}
