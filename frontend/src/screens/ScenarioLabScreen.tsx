import { useEffect, useMemo, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Badge, Button, Card, PanelHeader, Table, TableRow, Input, TextArea } from "react-bits";
import {
  PromoBrief,
  PromoScenario,
  ScenarioKPI,
  ValidationReport,
  createScenarioFromBrief,
  evaluateScenario,
  validateScenario,
} from "../api";
import { useUIStore } from "../store/uiStore";

type ScenarioRow = {
  scenario: PromoScenario;
  kpi?: ScenarioKPI;
  validation?: ValidationReport;
};

const defaultBrief: PromoBrief = {
  month: "2024-10",
  promo_date_range: { start_date: "2024-10-01", end_date: "2024-10-31" },
  focus_departments: ["TV", "GAMING"],
  objectives: { sales: 1.0 },
  constraints: { max_discount: 0.25, min_margin: 0.18 },
};

export default function ScenarioLabScreen() {
  const [brief, setBrief] = useState<PromoBrief>(defaultBrief);
  const [scenarioType, setScenarioType] = useState("balanced");
  const [scenarios, setScenarios] = useState<ScenarioRow[]>([]);
  const toggleScenario = useUIStore((s) => s.toggleActiveScenario);
  const setChatContext = useUIStore((s) => s.setChatContext);
  const [focusId, setFocusId] = useState<string | undefined>();

  const createMutation = useMutation({
    mutationFn: async () => {
      const sc = await createScenarioFromBrief(brief, scenarioType);
      const kpi = await evaluateScenario(sc);
      const validation = await validateScenario(sc);
      return { sc, kpi, validation };
    },
    onSuccess: ({ sc, kpi, validation }) => {
      setScenarios((prev) => [{ scenario: sc, kpi, validation }, ...prev]);
      setFocusId(sc.id || sc.label);
      setChatContext({ screen: "scenario", active_scenarios: [sc.id || ""], metadata: { month: brief.month, type: scenarioType } });
    },
  });

  useEffect(() => {
    if (!focusId && scenarios.length > 0) {
      setFocusId(scenarios[0].scenario.id || scenarios[0].scenario.label);
    }
  }, [focusId, scenarios]);

  const focusedScenario = useMemo(
    () => scenarios.find((row) => (row.scenario.id || row.scenario.label) === focusId),
    [focusId, scenarios]
  );

  const breakdownRows = useMemo(() => {
    if (!focusedScenario?.kpi) return [];
    const byDept = focusedScenario.kpi.breakdown_by_department || {};
    return Object.entries(byDept).map(([dept, metrics]) => ({
      dept,
      sales: metrics.sales || metrics.total_sales,
      margin: metrics.margin || metrics.total_margin,
      units: metrics.units || metrics.total_units,
    }));
  }, [focusedScenario?.kpi]);

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <PanelHeader title="Scenario configuration" eyebrow="Scenario Lab" />
        <div className="grid gap-3 md:grid-cols-2">
          <label className="flex flex-col gap-1 text-sm text-slate-700">
            <span className="text-xs text-muted">Month</span>
            <Input
              value={brief.month}
              onChange={(e) => setBrief({ ...brief, month: e.target.value })}
              aria-label="Month"
            />
          </label>
          <label className="flex flex-col gap-1 text-sm text-slate-700">
            <span className="text-xs text-muted">Promo window</span>
            <Input
              value={`${brief.promo_date_range?.start_date} → ${brief.promo_date_range?.end_date}`}
              onChange={(e) => {
                const [start, end] = e.target.value.split("→").map((v) => v.trim());
                setBrief({ ...brief, promo_date_range: { start_date: start || "", end_date: end || "" } });
              }}
              aria-label="Promo window"
            />
          </label>
          <label className="flex flex-col gap-1 text-sm text-slate-700">
            <span className="text-xs text-muted">Departments (comma separated)</span>
            <Input
              defaultValue={(brief.focus_departments || []).join(", ")}
              onChange={(e) => setBrief({ ...brief, focus_departments: e.target.value.split(",").map((d) => d.trim()).filter(Boolean) })}
              aria-label="Departments"
            />
          </label>
          <label className="flex flex-col gap-1 text-sm text-slate-700">
            <span className="text-xs text-muted">Scenario type</span>
            <select
              value={scenarioType}
              onChange={(e) => setScenarioType(e.target.value)}
              className="rounded-lg border border-border bg-white px-3 py-2 text-sm shadow-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-200"
            >
              <option value="balanced">Balanced</option>
              <option value="aggressive">Aggressive</option>
              <option value="conservative">Conservative</option>
            </select>
          </label>
          <label className="flex flex-col gap-1 text-sm text-slate-700 md:col-span-2">
            <span className="text-xs text-muted">Objectives / notes</span>
            <TextArea
              value={brief.objectives?.notes || "Drive sales uplift while holding 18% margin"}
              onChange={(e) =>
                setBrief({
                  ...brief,
                  objectives: { ...(brief.objectives || {}), notes: e.target.value },
                })
              }
              rows={3}
              aria-label="Objectives notes"
            />
          </label>
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          <Button onClick={() => createMutation.mutate()} disabled={createMutation.isPending}>
            {createMutation.isPending ? "Generating..." : "Create & Evaluate"}
          </Button>
        </div>
      </Card>

      <Card>
        <PanelHeader title="Scenario comparison" eyebrow="KPIs & validation" />
        {scenarios.length === 0 && <p className="text-sm text-muted">No scenarios yet. Generate one to compare KPIs.</p>}
        {scenarios.length > 0 && (
          <Table headers={["Scenario", "Sales", "Margin", "EBIT", "Status", "Select"]}>
            {scenarios.map((row) => (
              <TableRow key={row.scenario.id || row.scenario.label}>
                <div className="space-y-1">
                  <p className="font-semibold">{row.scenario.label || row.scenario.name || "Scenario"}</p>
                  <p className="text-xs text-muted">{row.scenario.scenario_type}</p>
                </div>
                <span>{Math.round(row.kpi?.total_sales || 0).toLocaleString()}</span>
                <span>{Math.round(row.kpi?.total_margin || 0).toLocaleString()}</span>
                <span>{Math.round(row.kpi?.total_ebit || 0).toLocaleString()}</span>
                <Badge tone={row.validation?.status === "PASS" ? "success" : row.validation?.status === "WARN" ? "warn" : "muted"}>
                  {row.validation?.status || "PENDING"}
                </Badge>
                <div className="flex flex-col gap-1">
                  <Button variant="ghost" size="sm" onClick={() => { toggleScenario(row.scenario.id || ""); setFocusId(row.scenario.id || row.scenario.label); }}>
                    Track
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => setFocusId(row.scenario.id || row.scenario.label)} aria-label="Focus scenario">
                    Details
                  </Button>
                </div>
              </TableRow>
            ))}
          </Table>
        )}
      </Card>

      {focusedScenario && (
        <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
          <Card>
            <PanelHeader
              title={focusedScenario.scenario.label || focusedScenario.scenario.name || "Scenario details"}
              eyebrow="KPI breakdown"
              action={<Badge tone="info">{focusedScenario.scenario.scenario_type}</Badge>}
            />
            {breakdownRows.length === 0 && <p className="text-sm text-muted">No breakdown data.</p>}
            {breakdownRows.length > 0 && (
              <Table headers={["Department", "Sales", "Margin", "Units"]}>
                {breakdownRows.map((row) => (
                  <TableRow key={row.dept}>
                    <span className="font-semibold">{row.dept}</span>
                    <span>{Math.round(row.sales || 0).toLocaleString()}</span>
                    <span>{Math.round(row.margin || 0).toLocaleString()}</span>
                    <span>{Math.round(row.units || 0).toLocaleString()}</span>
                  </TableRow>
                ))}
              </Table>
            )}
          </Card>

          <Card>
            <PanelHeader title="Validation" eyebrow="Readiness" />
            <div className="space-y-2">
              <Badge tone={focusedScenario.validation?.status === "PASS" ? "success" : focusedScenario.validation?.status === "WARN" ? "warn" : "muted"}>
                {focusedScenario.validation?.status || "PENDING"}
              </Badge>
              <p className="text-sm text-slate-700">Score: {Math.round((focusedScenario.validation?.overall_score || 0) * 100) / 100}</p>
              <div className="space-y-1">
                <p className="text-xs uppercase tracking-wide text-muted">Issues</p>
                <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700">
                  {(focusedScenario.validation?.issues || ["No issues found"]).map((issue) => (
                    <li key={issue}>{issue}</li>
                  ))}
                </ul>
              </div>
              {focusedScenario.validation?.fixes?.length ? (
                <div className="space-y-1">
                  <p className="text-xs uppercase tracking-wide text-muted">Suggested fixes</p>
                  <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700">
                    {focusedScenario.validation.fixes.map((fix) => (
                      <li key={fix}>{fix}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
