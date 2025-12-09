import { useMemo, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Button, Card, PanelHeader, Input, Badge } from "react-bits";
import { PostMortemReport, analyzePostMortem } from "../api";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useUIStore } from "../store/uiStore";
import { ClipboardList, Activity } from "lucide-react";

export default function PostMortemScreen() {
  const [scenarioId, setScenarioId] = useState("scenario_1");
  const [report, setReport] = useState<PostMortemReport | null>(null);
  const setChatContext = useUIStore((s) => s.setChatContext);

  const analyzeMutation = useMutation({
    mutationFn: async () => {
      const res = await analyzePostMortem(scenarioId);
      setReport(res);
      setChatContext({ screen: "postmortem", active_scenarios: [scenarioId] });
      return res;
    },
  });

  const accuracyData = useMemo(() => {
    if (!report?.forecast_accuracy) return [];
    return Object.entries(report.forecast_accuracy).map(([metric, value]) => ({ metric, value }));
  }, [report]);

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-col gap-2 rounded-2xl border border-border bg-white p-5 shadow-card">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs uppercase tracking-wide text-muted">Post-Mortem</p>
            <h1 className="text-2xl font-semibold text-slate-900">Campaign analysis</h1>
            <p className="text-sm text-muted">Compare forecast vs actual and capture learnings.</p>
          </div>
          <div className="inline-flex items-center gap-2 rounded-full bg-primary-50 px-3 py-1 text-xs font-semibold text-primary-700">
            <Activity className="h-4 w-4" />
            Accuracy check
          </div>
        </div>
      </div>

      <Card>
        <PanelHeader title="Post-Mortem Analysis" eyebrow="Completed campaigns" />
        <div className="grid gap-3 md:grid-cols-2">
          <label className="flex flex-col gap-1 text-sm text-slate-700">
            <span className="text-xs text-muted">Scenario ID</span>
            <Input value={scenarioId} onChange={(e) => setScenarioId(e.target.value)} aria-label="Scenario ID" />
          </label>
        </div>
        <div className="mt-3 flex gap-2">
          <Button onClick={() => analyzeMutation.mutate()} disabled={analyzeMutation.isPending}>
            {analyzeMutation.isPending ? "Analyzing..." : "Analyze"}
          </Button>
        </div>
      </Card>

      {report && (
        <>
          <div className="grid gap-3 md:grid-cols-3">
            <Card className="space-y-1">
              <p className="text-xs uppercase tracking-wide text-muted">Sales gap vs forecast</p>
              <p className="text-xl font-semibold text-slate-900">{(report as any)?.vs_forecast?.sales_value_error_pct ?? "—"}%</p>
            </Card>
            <Card className="space-y-1">
              <p className="text-xs uppercase tracking-wide text-muted">Margin gap vs forecast</p>
              <p className="text-xl font-semibold text-slate-900">{(report as any)?.vs_forecast?.margin_value_error_pct ?? "—"}%</p>
            </Card>
            <Card className="space-y-1">
              <p className="text-xs uppercase tracking-wide text-muted">EBIT gap vs forecast</p>
              <p className="text-xl font-semibold text-slate-900">{(report as any)?.vs_forecast?.ebit_error_pct ?? "—"}%</p>
            </Card>
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <PanelHeader title="Forecast vs Actual" eyebrow="Accuracy" />
              {accuracyData.length > 0 ? (
                <div className="h-64" aria-label="Forecast vs actual bar chart">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={accuracyData}>
                      <XAxis dataKey="metric" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="value" fill="#0ea5e9" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <p className="text-sm text-muted">No accuracy data.</p>
              )}
            </Card>
            <Card>
              <PanelHeader title="Insights" eyebrow="Learning memo" />
              <ul className="list-disc space-y-2 pl-4 text-sm text-slate-900">
                {report.insights.map((ins) => (
                  <li key={ins}>{ins}</li>
                ))}
              </ul>
              <div className="mt-3 flex flex-wrap gap-2">
                {report.cannibalization_signals?.map((c) => (
                  <Badge key={c} tone="warn">{c}</Badge>
                ))}
              </div>
              {typeof report.post_promo_dip === "number" && (
                <p className="mt-3 text-sm text-slate-700">Post-promo dip: {report.post_promo_dip}%</p>
              )}
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
