import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Area, AreaChart, CartesianGrid, Line, ResponsiveContainer, Tooltip, XAxis, YAxis, ReferenceLine } from "recharts";
import { Badge, Button, Card, PanelHeader } from "react-bits";
import { DiscoveryDashboard, fetchDiscoveryDashboard } from "../api";
import { useUIStore } from "../store/uiStore";

const months = ["2024-10", "2024-09"];
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
      <div className="h-64">
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
  const colorForGap = (gapPct: number) => {
    if (gapPct > 0.15) return "bg-amber-500";
    if (gapPct > 0.05) return "bg-orange-400";
    if (gapPct > -0.01) return "bg-green-500";
    return "bg-green-400";
  };

  return (
    <Card>
      <PanelHeader title="Gap heatmap" eyebrow="Departments" />
      <div className="mb-2 flex items-center gap-2 text-xs text-gray-600">
        <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-1 text-amber-700">+15% gap</span>
        <span className="inline-flex items-center gap-1 rounded-full bg-orange-100 px-2 py-1 text-orange-700">+5% gap</span>
        <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2 py-1 text-green-700">On target / ahead</span>
      </div>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
        {data.map((item) => (
          <div
            key={item.department}
            className={`rounded-xl p-3 text-white shadow-card transition hover:scale-[1.01] ${colorForGap(item.gap_pct)}`}
          >
            <div className="flex items-center justify-between text-sm font-semibold">
              <span>{item.department}</span>
              <span className="rounded-md bg-white/15 px-2 py-0.5 text-xs">Sales {currency(item.sales_value)}</span>
            </div>
            <div className="mt-2 text-2xl font-bold">{Math.round(item.gap_pct * 100)}%</div>
            <p className="text-xs text-white/80">Gap vs target</p>
          </div>
        ))}
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
      <div className="space-y-2 rounded-xl bg-gray-50 p-3">
        <p className="text-sm text-gray-700">{context.weather?.summary ?? "Weather data pending"}</p>
        {context.weather?.temperature && (
          <p className="text-xs text-gray-500">Temp: {context.weather.temperature} · Humidity: {context.weather.humidity}</p>
        )}
      </div>
      <div className="mt-3 space-y-2">
        <p className="text-xs uppercase tracking-wide text-gray-500">Events</p>
        <ul className="space-y-1 text-sm text-gray-900">
          {context.events?.map((event) => (
            <li key={`${event.name}-${event.date}`} className="flex items-center justify-between">
              <span className="font-medium">{event.name}</span>
              <span className="text-xs text-gray-500">{event.type} · {event.date}</span>
            </li>
          )) || <li>No events</li>}
        </ul>
      </div>
      <div className="mt-4 grid gap-2 md:grid-cols-2">
        <div>
          <p className="text-xs uppercase tracking-wide text-gray-500">Seasonality</p>
          <p className="text-sm text-gray-700">
            {Object.entries(context.seasonality?.weekly_patterns || {})
              .map(([k, v]) => `${k.substring(0, 3)} ${v}`)
              .join(", ") || "n/a"}
          </p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-wide text-gray-500">Weekend patterns</p>
          <p className="text-sm text-gray-700">
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
              selected === opp.id ? "border-primary-500 bg-primary-50" : "border-gray-200 hover:bg-gray-50"
            }`}
            aria-pressed={selected === opp.id}
          >
            <div>
              <p className="font-semibold text-gray-900">{opp.department} — {opp.channel}</p>
              <p className="text-sm text-gray-600">{opp.rationale}</p>
            </div>
            <Badge tone="success">+{currency(opp.estimated_potential)}</Badge>
          </button>
        ))}
      </div>
    </Card>
  );
}

function OpportunityDetails({ opportunity }: { opportunity?: DiscoveryDashboard["opportunities"][number] }) {
  if (!opportunity) return null;
  return (
    <Card>
      <PanelHeader title="Selected opportunity" eyebrow={opportunity.id} />
      <div className="space-y-2 text-sm text-gray-800">
        <div className="flex items-center gap-2">
          <Badge tone="info">{opportunity.department}</Badge>
          <Badge tone="muted">{opportunity.channel}</Badge>
        </div>
        <p className="font-semibold text-gray-900">{opportunity.rationale}</p>
        <p className="text-gray-600">
          Window: {opportunity.date_range.start_date} → {opportunity.date_range.end_date}
        </p>
        <p className="text-gray-700">Estimated potential: {currency(opportunity.estimated_potential)}</p>
      </div>
    </Card>
  );
}

export default function DiscoveryScreen() {
  const [month, setMonth] = useState("2024-10");
  const [geo, setGeo] = useState("DE");
  const setContext = useUIStore((s) => s.setChatContext);
  const setSelected = useUIStore((s) => s.setSelectedOpportunity);
  const selectedOpportunityId = useUIStore((s) => s.selectedOpportunityId);
  const monthLabel = new Date(`${month}-01`).toLocaleString("en-US", { month: "long", year: "numeric" });

  const dashboard = useQuery({
    queryKey: ["discovery-dashboard", month, geo],
    queryFn: () => fetchDiscoveryDashboard(month, geo),
    onSuccess: (data) => {
      setContext({ screen: "discovery", metadata: { geo: data.geo, month: data.month } });
    },
  });

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

  return (
    <div className="flex flex-col gap-3">
      <Card className="space-y-4">
        <PanelHeader title={`Discovery — ${monthLabel}`} eyebrow="Overview" />
        <div className="flex flex-wrap items-end gap-3">
          <label className="flex flex-col gap-1 text-sm text-gray-700">
            <span className="text-xs text-gray-500">Month</span>
            <select
              value={month}
              onChange={(e) => setMonth(e.target.value)}
              className="rounded-xl border border-gray-200 px-3 py-2 text-sm focus:border-primary-500 focus:ring-2 focus:ring-primary-200"
            >
              {months.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-sm text-gray-700">
            <span className="text-xs text-gray-500">Geo</span>
            <select
              value={geo}
              onChange={(e) => setGeo(e.target.value)}
              className="rounded-xl border border-gray-200 px-3 py-2 text-sm focus:border-primary-500 focus:ring-2 focus:ring-primary-200"
            >
              {geos.map((g) => (
                <option key={g} value={g}>{g}</option>
              ))}
            </select>
          </label>
          <Button onClick={() => dashboard.refetch()} disabled={dashboard.isFetching}>
            {dashboard.isFetching ? "Refreshing..." : "Refresh"}
          </Button>
        </div>
      </Card>

      {dashboard.isLoading && <Card>Loading discovery data...</Card>}
      {dashboard.error && <Card className="border-error-500 text-error-500">Failed to load discovery data.</Card>}

      {dashboard.data && (
        <>
          <div className="grid gap-3 md:grid-cols-3">
            {summaryCards.map((card) => (
              <Card key={card.label} className="space-y-1">
                <p className="text-sm text-gray-500">{card.label}</p>
                <div className="flex items-baseline gap-2">
                  <p className="text-2xl font-semibold text-gray-900">{card.value}</p>
                  {card.badge && <Badge tone="warn">{card.badge}</Badge>}
                </div>
              </Card>
            ))}
          </div>

          <GapVsTargetChart data={dashboard.data.gap_timeseries} month={month} />

          <div className="grid gap-3 lg:grid-cols-3">
            <DepartmentHeatmap data={dashboard.data.heatmap as HeatmapDatum[]} />
            <ContextWidget context={dashboard.data.context} />
            <OpportunitiesList
              opportunities={dashboard.data.opportunities}
              onSelect={(opp) => setSelected(opp.id)}
            />
          </div>

          <OpportunityDetails opportunity={selectedOpportunity} />
        </>
      )}
    </div>
  );
}
