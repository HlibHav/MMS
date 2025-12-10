import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Area, AreaChart, CartesianGrid, Line, ResponsiveContainer, Tooltip, XAxis, YAxis, ReferenceLine } from "recharts";
import { Badge, Button, Card, PanelHeader } from "react-bits";
import { BarChart3, MapPin, RefreshCw, Target } from "lucide-react";
import { DiscoveryDashboard, fetchDiscoveryDashboard, fetchDiscoveryMonths } from "../api";
import { useUIStore } from "../store/uiStore";

const geos = ["DE", "UA", "PL"];

const currency = (value?: number) => (typeof value === "number" ? value.toLocaleString("en-US", { maximumFractionDigits: 0 }) : "—");
const pct = (value?: number) => (typeof value === "number" ? `${(value * 100).toFixed(1)}%` : "—");

type HeatmapDatum = { department: string; gap_pct: number; sales_value: number };

function GapVsTargetChart({ data, month }: { data: DiscoveryDashboard["gap_timeseries"]; month: string }) {
  const chartData = data.map((d) => ({
    ...d,
    gap: Math.max((d.target ?? 0) - (d.actual ?? 0), 0),
  }));
  return (
    <Card>
      <PanelHeader title={`${month} daily trend`} eyebrow="Gap vs Target" />
      <div className="h-64" aria-label={`Gap vs Target for ${month}`}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="targetFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.18} />
                <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0.02} />
              </linearGradient>
              <linearGradient id="gapFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.26} />
                <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.05} />
              </linearGradient>
              <linearGradient id="actualFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#22c55e" stopOpacity={0.12} />
                <stop offset="95%" stopColor="#22c55e" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
            <XAxis dataKey="date" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip
              contentStyle={{ fontSize: 12 }}
              formatter={(value, name) => {
                if (name === "Gap") return [currency(value as number), "Gap to target"];
                return [currency(value as number), name === "target" ? "Target" : "Actual"];
              }}
            />
            <Area type="monotone" dataKey="gap" stackId="1" stroke="none" fill="url(#gapFill)" name="Gap" />
            <Area type="monotone" dataKey="actual" stackId="1" stroke="#22c55e" fill="url(#actualFill)" name="Actual" />
            <Line type="monotone" dataKey="target" stroke="#0284c7" dot={false} name="Target" strokeWidth={2} />
            <ReferenceLine y={0} stroke="#e5e7eb" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}

function DepartmentHeatmap({ data }: { data: HeatmapDatum[] }) {
  return (
    <Card className="bg-slate-900 border-slate-800 text-slate-100">
      <PanelHeader title="Department Heatmap" eyebrow="Gap vs target" />
      <div className="space-y-4">
        {data.map((item) => {
          const isPositive = item.gap_pct >= 0;
          const barColor = isPositive ? "bg-emerald-500" : "bg-rose-500";
          const textColor = isPositive ? "text-emerald-400" : "text-rose-400";
          return (
            <div key={item.department} className="space-y-2">
              <div className="flex items-center justify-between text-sm font-semibold">
                <span className="text-slate-100">{item.department}</span>
                <span className={`text-sm font-semibold ${textColor}`}>
                  {item.gap_pct > 0 ? "+" : ""}
                  {(item.gap_pct * 100).toFixed(1)}%
                </span>
              </div>
              <div className="h-2 w-full rounded-full bg-slate-800">
                <div
                  className={`h-2 rounded-full ${barColor}`}
                  style={{ width: `${Math.min(Math.abs(item.gap_pct) * 100, 100)}%` }}
                />
              </div>
              <p className="text-xs text-slate-400">Vol: {currency(item.sales_value)}</p>
            </div>
          );
        })}
      </div>
    </Card>
  );
}

function ContextWidget({ context }: { context: DiscoveryDashboard["context"] }) {
  return (
    <Card>
      <PanelHeader title="Context signals" eyebrow="Weather · Events · Patterns" />
      <div className="mb-3 flex flex-wrap gap-2">
        <Badge tone="info">{context.geo}</Badge>
        <Badge tone="muted">
          {context.date_range.start_date} → {context.date_range.end_date}
        </Badge>
      </div>
      <div className="space-y-2 rounded-xl bg-surface-50 p-3">
        <p className="text-sm text-slate-700">{context.weather?.summary ?? "Weather data pending"}</p>
        {context.weather?.temperature && (
          <p className="text-xs text-muted">Temp: {context.weather.temperature} · Humidity: {context.weather.humidity}</p>
        )}
      </div>
      <div className="mt-3 space-y-2">
        <p className="text-xs uppercase tracking-wide text-muted">Events</p>
        <ul className="space-y-1 text-sm text-slate-900">
          {context.events?.map((event) => (
            <li key={`${event.name}-${event.date}`} className="flex items-center justify-between">
              <span className="font-medium">{event.name}</span>
              <span className="text-xs text-muted">{event.type} · {event.date}</span>
            </li>
          )) || <li>No events</li>}
        </ul>
      </div>
      <div className="mt-4 grid gap-2 md:grid-cols-2">
        <div>
          <p className="text-xs uppercase tracking-wide text-muted">Seasonality</p>
          <p className="text-sm text-slate-700">
            {Object.entries(context.seasonality?.weekly_patterns || {})
              .map(([k, v]) => `${k.substring(0, 3)} ${v}`)
              .join(", ") || "n/a"}
          </p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-wide text-muted">Weekend patterns</p>
          <p className="text-sm text-slate-700">
            {Object.entries(context.weekend_patterns || {})
              .map(([k, v]) => `${k}: ${v}`)
              .join(", ") || "n/a"}
          </p>
        </div>
      </div>
    </Card>
  );
}

function OpportunitiesList({
  opportunities,
  onSelect,
}: {
  opportunities: DiscoveryDashboard["opportunities"];
  onSelect: (opportunity: DiscoveryDashboard["opportunities"][number]) => void;
}) {
  const selected = useUIStore((s) => s.selectedOpportunityId);
  return (
    <Card>
      <PanelHeader title="Top picks" eyebrow="Opportunities" />
      <div className="space-y-3">
        {opportunities.map((opp) => (
          <button
            key={opp.id}
            onClick={() => onSelect(opp)}
            className={`flex w-full items-start justify-between rounded-xl border px-3 py-2 text-left transition ${
              selected === opp.id ? "border-primary-500 bg-primary-50" : "border-border hover:bg-surface-50"
            }`}
            aria-pressed={selected === opp.id}
          >
            <div>
              <p className="font-semibold text-slate-900">
                {opp.title || opp.focus_departments?.join(", ") || opp.department || "Opportunity"} — {opp.channel || "mixed"}
              </p>
              <p className="text-sm text-slate-600">{opp.rationale}</p>
            </div>
            <Badge tone="success">
              +
              {currency(
                typeof opp.estimated_potential === "number"
                  ? opp.estimated_potential
                  : opp.estimated_potential?.sales_value
              )}
            </Badge>
          </button>
        ))}
      </div>
    </Card>
  );
}

function OpportunityDetails({ opportunity }: { opportunity?: DiscoveryDashboard["opportunities"][number] }) {
  if (!opportunity) return null;
  const windowStart = opportunity.promo_date_range?.start ?? opportunity.date_range?.start_date;
  const windowEnd = opportunity.promo_date_range?.end ?? opportunity.date_range?.end_date;
  const deptLabel = opportunity.focus_departments?.join(", ") || opportunity.department || "—";
  const channel = opportunity.channel || "mixed";
  const potential =
    typeof opportunity.estimated_potential === "number"
      ? opportunity.estimated_potential
      : opportunity.estimated_potential?.sales_value;
  return (
    <Card>
      <PanelHeader title="Selected opportunity" eyebrow={opportunity.id} />
      <div className="space-y-2 text-sm text-slate-800">
        <div className="flex items-center gap-2">
          <Badge tone="info">{deptLabel}</Badge>
          <Badge tone="muted">{channel}</Badge>
        </div>
        <p className="font-semibold text-slate-900">{opportunity.rationale}</p>
        {windowStart && windowEnd && (
          <p className="text-slate-600">
            Window: {windowStart} → {windowEnd}
          </p>
        )}
        <p className="text-slate-700">Estimated potential: {currency(potential)}</p>
      </div>
    </Card>
  );
}

export default function DiscoveryScreen() {
  const [month, setMonth] = useState<string | undefined>();
  const [geo, setGeo] = useState("DE");
  const setContext = useUIStore((s) => s.setChatContext);
  const setSelected = useUIStore((s) => s.setSelectedOpportunity);
  const selectedOpportunityId = useUIStore((s) => s.selectedOpportunityId);

  const monthsQuery = useQuery<string[]>({
    queryKey: ["discovery-months"],
    queryFn: fetchDiscoveryMonths,
  });

  useEffect(() => {
    if (!month && monthsQuery.data?.length) {
      setMonth(monthsQuery.data[0]);
    }
  }, [month, monthsQuery.data]);

  const monthLabel = month ? new Date(`${month}-01`).toLocaleString("en-US", { month: "long", year: "numeric" }) : "—";

  const dashboard = useQuery<DiscoveryDashboard, Error, DiscoveryDashboard, ["discovery-dashboard", string, string]>({
    queryKey: ["discovery-dashboard", month, geo],
    queryFn: () => fetchDiscoveryDashboard(month as string, geo),
    enabled: Boolean(month),
  });

  useEffect(() => {
    if (dashboard.data) {
      setContext({ screen: "discovery", metadata: { geo: dashboard.data.geo, month: dashboard.data.month } });
    }
  }, [dashboard.data, setContext]);

  useEffect(() => {
    if (!dashboard.data) return;
    if (selectedOpportunityId) return;
    const first = dashboard.data.opportunities?.[0];
    if (first) setSelected(first.id);
  }, [dashboard.data, selectedOpportunityId, setSelected]);

  useEffect(() => {
    if (selectedOpportunityId) {
      const selected = dashboard.data?.opportunities.find((o) => o.id === selectedOpportunityId);
      setContext({
        metadata: {
          ...dashboard.data?.summary,
          selectedOpportunityId,
          selectedOpportunityDepartment: selected?.department,
        },
      });
    }
  }, [dashboard.data?.opportunities, dashboard.data?.summary, selectedOpportunityId, setContext]);

  const summaryCards = useMemo(() => {
    const data = dashboard.data?.summary;
    if (!data) return [];
    return [
      { label: "Sales gap", value: currency(data.sales_gap), badge: data.gap_percentage?.sales && pct(data.gap_percentage.sales) },
      { label: "Margin gap", value: pct(data.margin_gap), badge: data.gap_percentage?.margin && pct(data.gap_percentage.margin) },
      { label: "Units gap", value: currency(data.units_gap ?? 0), badge: data.gap_percentage?.units && pct(data.gap_percentage.units) },
    ];
  }, [dashboard.data]);

  const selectedOpportunity = dashboard.data?.opportunities.find((o) => o.id === selectedOpportunityId);

  const darkCard = "bg-slate-900 border border-slate-800 text-slate-100";

  return (
    <div className="min-h-screen bg-slate-950 px-4 py-6 text-slate-100 md:px-8">
      <div className={`flex flex-col gap-3 rounded-2xl p-5 shadow-card ${darkCard}`}>
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-400">Discovery</p>
            <h1 className="text-2xl font-semibold text-slate-50">{monthLabel}</h1>
            <p className="text-sm text-slate-400">Overview of gaps, context signals and top opportunities.</p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              className="border border-slate-700 bg-slate-800 text-slate-100 hover:bg-slate-700"
              onClick={() => dashboard.refetch()}
              disabled={dashboard.isFetching}
              aria-label="Refresh"
            >
              <RefreshCw className="h-4 w-4" />
              <span className="ml-1">{dashboard.isFetching ? "Refreshing..." : "Refresh"}</span>
            </Button>
          </div>
        </div>
        <div className="grid gap-3 sm:grid-cols-[repeat(auto-fit,minmax(160px,1fr))]">
          <div className="rounded-xl border border-slate-800 bg-slate-900 p-3">
            <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-slate-400">
              <Target className="h-4 w-4 text-primary-400" />
              <span>Month</span>
            </div>
            <select
              value={month ?? ""}
              onChange={(e) => setMonth(e.target.value)}
              disabled={monthsQuery.isLoading || monthsQuery.isError || !monthsQuery.data?.length}
              className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-100 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {monthsQuery.data?.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
            {monthsQuery.isError && <p className="mt-2 text-xs text-error-400">Не вдалося завантажити місяці</p>}
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-900 p-3">
            <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-slate-400">
              <MapPin className="h-4 w-4 text-primary-400" />
              <span>Geo</span>
            </div>
            <select
              value={geo}
              onChange={(e) => setGeo(e.target.value)}
              className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-100 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              {geos.map((g) => (
                <option key={g} value={g}>{g}</option>
              ))}
            </select>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-900 p-3">
            <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-slate-400">
              <BarChart3 className="h-4 w-4 text-primary-400" />
              <span>Summary</span>
            </div>
            <p className="mt-2 text-sm text-slate-200">Discovery insights for {geo}</p>
          </div>
        </div>
      </div>

      {dashboard.isLoading && <Card>Loading discovery data...</Card>}
      {dashboard.error && <Card className="border-error-500 text-error-600">Failed to load discovery data.</Card>}

      {dashboard.data && (
        <>
          <div className="grid gap-4 md:grid-cols-3">
            {summaryCards.map((card) => (
              <Card key={card.label} className={`space-y-2 shadow-card ${darkCard}`}>
                <p className="text-xs uppercase tracking-wide text-slate-400">{card.label}</p>
                <div className="flex items-center gap-3">
                  <p className="text-2xl font-semibold text-slate-50">{card.value}</p>
                  {card.badge && <Badge tone="warn">{card.badge}</Badge>}
                </div>
              </Card>
            ))}
          </div>

          <Card className={`shadow-card ${darkCard}`}>
            <PanelHeader title="Performance gap analysis" eyebrow="Actual vs Target" />
            <GapVsTargetChart data={dashboard.data.gap_timeseries} month={month ?? ""} />
          </Card>

          <div className="grid gap-4 lg:grid-cols-3">
            <Card className={darkCard}>
              <DepartmentHeatmap data={dashboard.data.heatmap as HeatmapDatum[]} />
            </Card>
            <Card className={darkCard}>
              <ContextWidget context={dashboard.data.context} />
            </Card>
            <Card className={darkCard}>
              <OpportunitiesList
                opportunities={dashboard.data.opportunities}
                onSelect={(opp) => setSelected(opp.id)}
              />
            </Card>
          </div>

          <Card className={darkCard}>
            <OpportunityDetails opportunity={selectedOpportunity} />
          </Card>
        </>
      )}
    </div>
  );
}
