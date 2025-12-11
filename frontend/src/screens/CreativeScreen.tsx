import { useMemo, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Button, Card, PanelHeader, Badge, Input, TextArea } from "react-bits";
import { Sparkles, FileText } from "lucide-react";
import { AssetSpec, CreativeBrief, PromoScenario, generateCreativeAssets, generateCreativeBrief } from "../api";
import { useUIStore } from "../store/uiStore";

export default function CreativeScreen() {
  const [scenarioId, setScenarioId] = useState("scenario_1");
  const [scenario, setScenario] = useState<PromoScenario | null>(null);
  const [brief, setBrief] = useState<CreativeBrief | null>(null);
  const [assets, setAssets] = useState<AssetSpec[]>([]);
  const [notes, setNotes] = useState("Highlight urgency and value in copy.");
  const setChatContext = useUIStore((s) => s.setChatContext);

  const briefMutation = useMutation({
    mutationFn: async () => {
      const sc: PromoScenario = {
        id: scenarioId,
        label: `Scenario ${scenarioId}`,
        date_range: { start_date: "2024-10-01", end_date: "2024-10-31" },
        departments: ["TV"],
        channels: ["online"],
      };
      setScenario(sc);
      const b = await generateCreativeBrief(sc);
      setBrief(b);
      setChatContext({ screen: "creative", active_scenarios: [scenarioId] });
      return b;
    },
  });

  const assetsMutation = useMutation({
    mutationFn: async () => {
      if (!brief) return [] as AssetSpec[];
      const a = await generateCreativeAssets(brief);
      setAssets(a);
      return a;
    },
  });

  const briefMeta = useMemo(
    () => ({
      objectives: brief?.objectives?.join(", "),
      tone: brief?.tone,
      target_audience: brief?.target_audience,
    }),
    [brief]
  );

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-col gap-2 rounded-2xl border border-border bg-white p-5 shadow-card">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs uppercase tracking-wide text-muted">Creative Companion</p>
            <h1 className="text-2xl font-semibold text-slate-900">Brief & assets</h1>
            <p className="text-sm text-muted">Generate briefs and assets for selected scenario.</p>
          </div>
          <div className="inline-flex items-center gap-2 rounded-full bg-primary-50 px-3 py-1 text-xs font-semibold text-primary-700">
            <Sparkles className="h-4 w-4" /> AI assisted
          </div>
        </div>
      </div>

      <Card className="space-y-4">
        <PanelHeader title="Creative Brief" eyebrow="Inputs" />
        <div className="grid gap-3 md:grid-cols-2">
          <label className="flex flex-col gap-1 text-sm text-slate-700">
            <span className="text-xs text-muted">Scenario ID</span>
            <Input value={scenarioId} onChange={(e) => setScenarioId(e.target.value)} aria-label="Scenario ID" />
          </label>
          <label className="flex flex-col gap-1 text-sm text-slate-700">
            <span className="text-xs text-muted">Notes to emphasize</span>
            <TextArea rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} aria-label="Creative notes inline" />
          </label>
        </div>
        <div className="mt-2 flex flex-wrap gap-2">
          <Button onClick={() => briefMutation.mutate()} disabled={briefMutation.isPending}>
            {briefMutation.isPending ? "Generating..." : "Generate Brief"}
          </Button>
          <Button variant="ghost" onClick={() => assetsMutation.mutate()} disabled={!brief || assetsMutation.isPending}>
            {assetsMutation.isPending ? "Creating..." : "Generate Assets"}
          </Button>
        </div>
      </Card>

      {brief && (
        <Card className="space-y-4">
          <PanelHeader title="Brief details" eyebrow="Draft" />
          <div className="grid gap-3 md:grid-cols-3 text-sm text-slate-800">
            <div className="rounded-xl border border-border bg-surface-50 p-3">
              <p className="text-xs uppercase tracking-wide text-muted">Objectives</p>
              <p className="font-semibold text-slate-900">{briefMeta.objectives || "n/a"}</p>
            </div>
            <div className="rounded-xl border border-border bg-surface-50 p-3">
              <p className="text-xs uppercase tracking-wide text-muted">Tone</p>
              <p className="font-semibold text-slate-900">{briefMeta.tone || "n/a"}</p>
            </div>
            <div className="rounded-xl border border-border bg-surface-50 p-3">
              <p className="text-xs uppercase tracking-wide text-muted">Audience</p>
              <p className="font-semibold text-slate-900">{briefMeta.target_audience || "n/a"}</p>
            </div>
          </div>
          <p className="text-sm text-slate-900">{brief.messaging}</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {brief.mandatory_elements.map((el) => (
              <Badge key={el} tone="muted">{el}</Badge>
            ))}
          </div>
          <div className="mt-4">
            <p className="text-xs uppercase tracking-wide text-muted">Notes</p>
            <TextArea value={notes} onChange={(e) => setNotes(e.target.value)} rows={3} aria-label="Creative notes" />
          </div>
        </Card>
      )}

      {assets.length > 0 && (
        <Card className="space-y-3">
          <PanelHeader title="Generated assets" eyebrow="Copy & layout" />
          <div className="grid gap-3 md:grid-cols-3">
            {assets.map((asset) => {
              const handleCopy = () => navigator.clipboard?.writeText(asset.copy_text);
              const handleExport = () => {
                const blob = new Blob([asset.copy_text], { type: "text/plain" });
                const url = URL.createObjectURL(blob);
                const link = document.createElement("a");
                link.href = url;
                link.download = `${asset.asset_type}.txt`;
                link.click();
                URL.revokeObjectURL(url);
              };
              return (
                <div key={asset.asset_type} className="rounded-xl border border-border bg-surface-50 p-3">
                  <div className="flex items-center justify-between text-xs uppercase tracking-wide text-muted">
                    <span>{asset.asset_type}</span>
                    <FileText className="h-4 w-4 text-primary-600" />
                  </div>
                  <p className="mt-2 text-sm text-slate-900 whitespace-pre-wrap">{asset.copy_text}</p>
                  <div className="mt-3 flex gap-2">
                    <Button variant="ghost" size="sm" onClick={handleCopy} aria-label={`Copy ${asset.asset_type} copy`}>
                      Copy
                    </Button>
                    <Button variant="ghost" size="sm" onClick={handleExport} aria-label={`Export ${asset.asset_type} copy`}>
                      Export
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      )}
      {assetsMutation.isPending && <p className="text-sm text-muted">Generating assets…</p>}
      {assets.length === 0 && !assetsMutation.isPending && brief && <p className="text-sm text-muted">No assets yet. Generate to see copy.</p>}
    </div>
  );
}
