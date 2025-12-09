import { useMemo, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Button, Card, PanelHeader, Input, Badge } from "react-bits";
import { PostMortemReport, analyzePostMortem } from "../api";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useUIStore } from "../store/uiStore";

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
    <div className="flex flex-col gap-4">
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
        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <PanelHeader title="Forecast vs Actual" eyebrow="Accuracy" />
            {accuracyData.length > 0 ? (
              <div className="h-64">
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
      )}
    </div>
  );
}
