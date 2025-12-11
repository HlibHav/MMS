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
import { cn } from "../utils/format";

type ScenarioRow = {
  scenario: PromoScenario;
  kpi?: ScenarioKPI;
  validation?: ValidationReport;
};

type ScenarioForm = {
  scenario_name: string;
  month: string;
  start_date: string;
  end_date: string;
  departments: string[];
  scenario_type: string;
  objectives_notes: string;
  department_discounts: Record<string, number>;
  min_margin: number;
};

export default function ScenarioLabScreen() {
  const departmentOptions = ["Electronics", "Fashion", "Home", "Sports", "Beauty", "Toys"];
  const [scenarios, setScenarios] = useState<ScenarioRow[]>([]);
  const toggleScenario = useUIStore((s) => s.toggleActiveScenario);
  const setChatContext = useUIStore((s) => s.setChatContext);
  const [focusId, setFocusId] = useState<string | undefined>();

  const form = useForm<ScenarioForm>({
    defaultValues: {
      scenario_name: "Conservative Push",
      month: "2024-10",
      start_date: "2024-10-01",
      end_date: "2024-10-31",
      departments: ["Electronics"],
      scenario_type: "balanced",
      objectives_notes: "Drive sales uplift while holding 18% margin",
      department_discounts: { Electronics: 10 },
      min_margin: 18,
    },
  });

  const createMutation = useMutation({
    mutationFn: async (values: ScenarioForm) => {
      const brief: PromoBrief = {
        month: values.month,
        // Backend expects `start`/`end` for promo_date_range
        promo_date_range: { start: values.start_date, end: values.end_date },
        focus_departments: values.departments,
        objectives: { notes: values.objectives_notes, name: values.scenario_name },
        constraints: {
          department_discounts: values.department_discounts,
          min_margin: values.min_margin / 100,
        },
      };
      const parameters = {
        label: values.scenario_name,
        name: values.scenario_name,
        department_discounts: values.department_discounts,
      };
      const created = await createScenarioFromBrief(brief, values.scenario_type, parameters);
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
          <form onSubmit={form.handleSubmit((values) => createMutation.mutate(values))} className="space-y-5">
            <PanelHeader title="Configuration" eyebrow="Scenario Lab" />

            <div className="space-y-4">
              <div className="space-y-2">
                <label className="flex flex-col gap-1 text-sm text-slate-700">
                  <span className="text-xs text-muted">Scenario name</span>
                  <Input aria-label="Scenario name" {...form.register("scenario_name")} />
                </label>
              </div>

              <div className="grid gap-3 md:grid-cols-3">
                <label className="flex flex-col gap-1 text-sm text-slate-700">
                  <span className="text-xs text-muted">Month</span>
                  <Input aria-label="Month" {...form.register("month")} />
                </label>
                <label className="flex flex-col gap-1 text-sm text-slate-700">
                  <span className="text-xs text-muted">Start date</span>
                  <Input type="date" aria-label="Start date" {...form.register("start_date")} />
                </label>
                <label className="flex flex-col gap-1 text-sm text-slate-700">
                  <span className="text-xs text-muted">End date</span>
                  <Input type="date" aria-label="End date" {...form.register("end_date")} />
                </label>
              </div>

              <div className="space-y-2">
                <span className="text-xs text-muted uppercase tracking-wide">Active departments</span>
                <div className="grid grid-cols-2 gap-2 md:grid-cols-3">
                  {departmentOptions.map((dept) => {
                    const selected = form.watch("departments").includes(dept);
                    return (
                      <button
                        type="button"
                        key={dept}
                        className={`rounded-lg border px-3 py-2 text-sm ${
                          selected ? "border-primary-500 bg-primary-50 text-primary-700 shadow-inner" : "border-border bg-white text-slate-800 hover:border-primary-300"
                        }`}
                        onClick={() => {
                          const current = form.getValues("departments");
                          const next = current.includes(dept) ? current.filter((d) => d !== dept) : [...current, dept];
                          form.setValue("departments", next, { shouldDirty: true });
                          const discounts = form.getValues("department_discounts") || {};
                          if (!next.includes(dept)) {
                            delete discounts[dept];
                          } else {
                            discounts[dept] = discounts[dept] ?? 10;
                          }
                          form.setValue("department_discounts", { ...discounts }, { shouldDirty: true });
                        }}
                      >
                        {dept}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs text-muted">
                  <span className="uppercase tracking-wide">Discount levels by department</span>
                </div>
                <div className="space-y-3 rounded-lg border border-border bg-white px-3 py-3">
                  {form.watch("departments").length === 0 && <p className="text-sm text-muted">Select a department to set discount.</p>}
                  {form.watch("departments").map((dept) => (
                    <div key={dept} className="space-y-2">
                      <div className="flex items-center justify-between text-sm font-semibold text-slate-800">
                        <span>{dept}</span>
                        <span className="text-xs text-muted">{form.watch("department_discounts")[dept] ?? 0}%</span>
                      </div>
                      <input
                        type="range"
                        min={0}
                        max={100}
                        step={1}
                        aria-label={`${dept} discount`}
                        value={form.watch("department_discounts")[dept] ?? 0}
                        onChange={(e) => {
                          const discounts = { ...(form.getValues("department_discounts") || {}) };
                          discounts[dept] = Number(e.target.value);
                          form.setValue("department_discounts", discounts, { shouldDirty: true });
                        }}
                        className="w-full accent-primary-600"
                      />
                    </div>
                  ))}
                </div>
              </div>

              <div className="grid gap-3 md:grid-cols-2">
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
                  <span className="text-xs text-muted">Min margin (%)</span>
                  <Input type="number" min={0} max={100} step={1} aria-label="Min margin" {...form.register("min_margin", { valueAsNumber: true })} />
                </label>
              </div>

              <label className="flex flex-col gap-1 text-sm text-slate-700">
                <span className="text-xs text-muted">Objectives / notes</span>
                <TextArea rows={3} aria-label="Objectives notes" {...form.register("objectives_notes")} />
              </label>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <Button type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending ? "Generating..." : "Save & Evaluate"}
              </Button>
            </div>
          </form>
        </Card>

        <Card>
          <PanelHeader title="Scenario comparison" eyebrow="KPIs & validation" />
          {scenarios.length === 0 && <p className="text-sm text-muted">No scenarios yet. Generate one to compare KPIs.</p>}
          {scenarios.length > 0 && (
            <div className="overflow-hidden rounded-2xl border border-slate-800 bg-slate-950 text-slate-100">
              <div className="grid grid-cols-[1.2fr_0.9fr_0.9fr_0.8fr_0.8fr] items-center border-b border-slate-800 px-5 py-3 text-xs font-semibold uppercase tracking-wide text-slate-400">
                <span>Scenario name</span>
                <span>Sales</span>
                <span>Margin</span>
                <span>EBIT</span>
                <span className="text-center">Status</span>
              </div>
              <div className="divide-y divide-slate-800">
                {scenarios.map((row, idx) => {
                  const isFocused = (row.scenario.id || row.scenario.label) === focusId;
                  const status = (row.validation?.status as "PASS" | "WARN" | "BLOCK") || "BLOCK";
                  const statusColor =
                    status === "PASS" ? "bg-emerald-500/20 text-emerald-200 ring-emerald-400/40" :
                    status === "WARN" ? "bg-amber-500/20 text-amber-200 ring-amber-400/40" :
                    "bg-rose-500/20 text-rose-200 ring-rose-400/40";
                  const marginPct = row.kpi?.total_margin && row.kpi?.total_sales
                    ? `${((row.kpi.total_margin / row.kpi.total_sales) * 100).toFixed(1)}%`
                    : "–";
                  const salesFmt = `$${Math.round(row.kpi?.total_sales || 0).toLocaleString()}`;
                  const ebitFmt = `$${Math.round(row.kpi?.total_ebit || 0).toLocaleString()}`;
                  const issuesTooltip = (row.validation?.issues || [])
                    .map((i: any) => (typeof i === "string" ? i : i?.message))
                    .filter(Boolean)
                    .join("\n");
                  const rowTooltip = [
                    row.scenario.label || row.scenario.name || "Scenario",
                    `Departments: ${row.scenario.departments?.join(", ") || "N/A"}`,
                    `Channels: ${row.scenario.channels?.join(", ") || "All"}`,
                  ].join("\n");
                  return (
                    <div
                      key={row.scenario.id || row.scenario.label || idx}
                      className={cn(
                        "grid grid-cols-[1.2fr_0.9fr_0.9fr_0.8fr_0.8fr] items-center px-5 py-4",
                        isFocused ? "bg-white/5" : "hover:bg-white/5/40"
                      )}
                      title={rowTooltip}
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="h-8 w-1 rounded-full bg-primary-400" aria-hidden />
                          <p className="font-semibold text-slate-50">{row.scenario.label || row.scenario.name || "Scenario"}</p>
                        </div>
                        <p className="pl-3 text-xs text-slate-400">
                          {row.scenario.departments?.length || 0} depts • {row.scenario.channels?.join(", ") || "All"}
                        </p>
                      </div>
                      <div className="text-sm font-semibold text-slate-50">{salesFmt}</div>
                      <div className="text-sm font-semibold text-slate-50">{marginPct}</div>
                      <div className="text-sm font-semibold text-slate-50">{ebitFmt}</div>
                      <div className="flex items-center justify-center gap-3">
                        <div
                          className={cn(
                            "flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold ring-1 ring-inset",
                            statusColor
                          )}
                          title={issuesTooltip || status}
                        >
                          {status === "PASS" ? "✔" : status === "WARN" ? "!" : "✖"} <span className="uppercase">{status}</span>
                        </div>
                        <Button
                          variant={isFocused ? "secondary" : "ghost"}
                          size="sm"
                          onClick={() => setFocusId(row.scenario.id || row.scenario.label)}
                          aria-label="Focus scenario"
                        >
                          {isFocused ? "Focused" : "Details"}
                        </Button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
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
                  {(focusedScenario.validation?.issues || ["No issues found"]).map((issue: any, idx) => {
                    const text = typeof issue === "string" ? issue : issue?.message || JSON.stringify(issue);
                    return <li key={typeof issue === "string" ? issue : `${issue?.type || "issue"}-${idx}`}>{text}</li>;
                  })}
                </ul>
              </div>
              {focusedScenario.validation?.fixes?.length ? (
                <div className="space-y-1">
                  <p className="text-xs uppercase tracking-wide text-muted">Suggested fixes</p>
                  <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700">
                    {focusedScenario.validation.fixes.map((fix, idx) => (
                      <li key={typeof fix === "string" ? fix : idx}>{fix}</li>
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
