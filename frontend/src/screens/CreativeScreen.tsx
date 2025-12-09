import { useMemo, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Button, Card, PanelHeader, Badge, Input, TextArea } from "react-bits";
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
    <div className="flex flex-col gap-3">
      <Card>
        <PanelHeader title="Creative Brief" eyebrow="Creative Companion" />
        <div className="grid gap-3 md:grid-cols-2">
          <label className="flex flex-col gap-1 text-sm text-gray-700">
            <span className="text-xs text-gray-500">Scenario ID</span>
            <Input value={scenarioId} onChange={(e) => setScenarioId(e.target.value)} aria-label="Scenario ID" />
          </label>
        </div>
        <div className="mt-3 flex gap-2">
          <Button onClick={() => briefMutation.mutate()} disabled={briefMutation.isPending}>
            {briefMutation.isPending ? "Generating..." : "Generate Brief"}
          </Button>
          <Button variant="ghost" onClick={() => assetsMutation.mutate()} disabled={!brief || assetsMutation.isPending}>
            {assetsMutation.isPending ? "Creating..." : "Generate Assets"}
          </Button>
        </div>
      </Card>

      {brief && (
        <Card>
          <PanelHeader title="Brief details" eyebrow="Draft" />
          <div className="grid gap-3 md:grid-cols-3 text-sm text-gray-800">
            <div className="rounded-xl border border-gray-200 bg-gray-50 p-3">
              <p className="text-xs uppercase tracking-wide text-gray-500">Objectives</p>
              <p className="font-semibold text-gray-900">{briefMeta.objectives || "n/a"}</p>
            </div>
            <div className="rounded-xl border border-gray-200 bg-gray-50 p-3">
              <p className="text-xs uppercase tracking-wide text-gray-500">Tone</p>
              <p className="font-semibold text-gray-900">{briefMeta.tone || "n/a"}</p>
            </div>
            <div className="rounded-xl border border-gray-200 bg-gray-50 p-3">
              <p className="text-xs uppercase tracking-wide text-gray-500">Audience</p>
              <p className="font-semibold text-gray-900">{briefMeta.target_audience || "n/a"}</p>
            </div>
          </div>
          <p className="mt-3 text-sm text-gray-900">{brief.messaging}</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {brief.mandatory_elements.map((el) => (
              <Badge key={el} tone="muted">{el}</Badge>
            ))}
          </div>
          <div className="mt-4">
            <p className="text-xs uppercase tracking-wide text-gray-500">Notes</p>
            <TextArea value={notes} onChange={(e) => setNotes(e.target.value)} rows={3} aria-label="Creative notes" />
          </div>
        </Card>
      )}

      {assets.length > 0 && (
        <Card>
          <PanelHeader title="Generated assets" eyebrow="Copy & layout" />
          <div className="grid gap-2 md:grid-cols-3">
            {assets.map((asset) => (
              <div key={asset.asset_type} className="rounded-xl border border-gray-200 p-3">
                <p className="text-xs uppercase tracking-wide text-gray-500">{asset.asset_type}</p>
                <p className="text-sm text-gray-900 whitespace-pre-wrap">{asset.copy_text}</p>
                <Button variant="ghost" size="sm" className="mt-2">Copy</Button>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
