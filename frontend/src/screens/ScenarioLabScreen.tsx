import { useEffect, useMemo, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { Badge, Button, Card, PanelHeader, Table, TableRow, Input, TextArea, ValidationIndicator } from "react-bits";
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

type ScenarioForm = {
  month: string;
  start_date: string;
  end_date: string;
  departments: string;
  scenario_type: string;
  objectives_notes: string;
  max_discount: number;
  min_margin: number;
};

export default function ScenarioLabScreen() {
  const [scenarios, setScenarios] = useState<ScenarioRow[]>([]);
  const toggleScenario = useUIStore((s) => s.toggleActiveScenario);
  const setChatContext = useUIStore((s) => s.setChatContext);
  const [focusId, setFocusId] = useState<string | undefined>();

  const form = useForm<ScenarioForm>({
    defaultValues: {
      month: "2024-10",
      start_date: "2024-10-01",
      end_date: "2024-10-31",
      departments: "TV, GAMING",
      scenario_type: "balanced",
      objectives_notes: "Drive sales uplift while holding 18% margin",
      max_discount: 25,
      min_margin: 18,
    },
  });

  const createMutation = useMutation({
    mutationFn: async (values: ScenarioForm) => {
      const brief: PromoBrief = {
        month: values.month,
        promo_date_range: { start_date: values.start_date, end_date: values.end_date },
        focus_departments: values.departments.split(",").map((d) => d.trim()).filter(Boolean),
        objectives: { notes: values.objectives_notes },
        constraints: { max_discount: values.max_discount / 100, min_margin: values.min_margin / 100 },
      };
      const created = await createScenarioFromBrief(brief, values.scenario_type);
      const sc: PromoScenario = created?.scenario ?? (created as any);
      const kpi = created?.kpi ?? (sc ? await evaluateScenario(sc) : undefined);
      const validation = created?.validation ?? (sc ? await validateScenario(sc) : undefined);
      return { sc, kpi, validation, values };
    },
    onSuccess: ({ sc, kpi, validation, values }) => {
      setScenarios((prev) => [{ scenario: sc, kpi, validation }, ...prev]);
      setFocusId(sc.id || sc.label);
      setChatContext({ screen: "scenario", active_scenarios: [sc.id || ""], metadata: { month: values.month, type: values.scenario_type } });
      form.reset({ ...values, departments: values.departments });
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
    <div className="flex flex-col gap-5">
      <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
        <Card>
          <form onSubmit={form.handleSubmit((values) => createMutation.mutate(values))} className="space-y-4">
            <PanelHeader title="Scenario configuration" eyebrow="Scenario Lab" />
            <div className="grid gap-3 md:grid-cols-2">
              <label className="flex flex-col gap-1 text-sm text-slate-700">
                <span className="text-xs text-muted">Month</span>
                <Input aria-label="Month" {...form.register("month")} />
              </label>
              <div className="grid grid-cols-2 gap-2">
                <label className="flex flex-col gap-1 text-sm text-slate-700">
                  <span className="text-xs text-muted">Start date</span>
                  <Input type="date" aria-label="Start date" {...form.register("start_date")} />
                </label>
                <label className="flex flex-col gap-1 text-sm text-slate-700">
                  <span className="text-xs text-muted">End date</span>
                  <Input type="date" aria-label="End date" {...form.register("end_date")} />
                </label>
              </div>
              <label className="flex flex-col gap-1 text-sm text-slate-700">
                <span className="text-xs text-muted">Departments (comma separated)</span>
                <Input aria-label="Departments" {...form.register("departments")} />
              </label>
              <label className="flex flex-col gap-1 text-sm text-slate-700">
                <span className="text-xs text-muted">Scenario type</span>
                <select
                  aria-label="Scenario type"
                  className="rounded-lg border border-border bg-white px-3 py-2 text-sm shadow-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-200"
                  {...form.register("scenario_type")}
                >
                  <option value="balanced">Balanced</option>
                  <option value="aggressive">Aggressive</option>
                  <option value="conservative">Conservative</option>
                </select>
              </label>
              <label className="flex flex-col gap-1 text-sm text-slate-700">
                <span className="text-xs text-muted">Max discount (%)</span>
                <Input type="number" min={0} max={100} step={1} aria-label="Max discount" {...form.register("max_discount", { valueAsNumber: true })} />
              </label>
              <label className="flex flex-col gap-1 text-sm text-slate-700">
                <span className="text-xs text-muted">Min margin (%)</span>
                <Input type="number" min={0} max={100} step={1} aria-label="Min margin" {...form.register("min_margin", { valueAsNumber: true })} />
              </label>
              <label className="flex flex-col gap-1 text-sm text-slate-700 md:col-span-2">
                <span className="text-xs text-muted">Objectives / notes</span>
                <TextArea rows={3} aria-label="Objectives notes" {...form.register("objectives_notes")} />
              </label>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending ? "Generating..." : "Create & Evaluate"}
              </Button>
            </div>
          </form>
        </Card>

        <Card>
          <PanelHeader title="Scenario comparison" eyebrow="KPIs & validation" />
          {scenarios.length === 0 && <p className="text-sm text-muted">No scenarios yet. Generate one to compare KPIs.</p>}
          {scenarios.length > 0 && (
            <Table headers={["Scenario", "Sales", "Margin", "EBIT", "Status", "Select"]}>
              {scenarios.map((row) => {
                const isFocused = (row.scenario.id || row.scenario.label) === focusId;
                return (
                  <TableRow key={row.scenario.id || row.scenario.label}>
                    <div className="space-y-1">
                      <p className="font-semibold">{row.scenario.label || row.scenario.name || "Scenario"}</p>
                      <p className="text-xs text-muted">{row.scenario.scenario_type}</p>
                    </div>
                    <span>{Math.round(row.kpi?.total_sales || 0).toLocaleString()}</span>
                    <span>{Math.round(row.kpi?.total_margin || 0).toLocaleString()}</span>
                    <span>{Math.round(row.kpi?.total_ebit || 0).toLocaleString()}</span>
                    <ValidationIndicator status={(row.validation?.status as "PASS" | "WARN" | "BLOCK") || "BLOCK"} label={row.validation?.status || "PENDING"} />
                    <div className="flex flex-col gap-1">
                      <Button
                        variant={isFocused ? "secondary" : "ghost"}
                        size="sm"
                        onClick={() => {
                          toggleScenario(row.scenario.id || "");
                          setFocusId(row.scenario.id || row.scenario.label);
                        }}
                      >
                        {isFocused ? "Focused" : "Track"}
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => setFocusId(row.scenario.id || row.scenario.label)} aria-label="Focus scenario">
                        Details
                      </Button>
                    </div>
                  </TableRow>
                );
              })}
            </Table>
          )}
        </Card>
      </div>

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
              <ValidationIndicator
                status={(focusedScenario.validation?.status as "PASS" | "WARN" | "BLOCK") || "BLOCK"}
                label={focusedScenario.validation?.status || "PENDING"}
              />
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
