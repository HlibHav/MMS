export default function AssetCard({ asset }: { asset: any }) {
  return (
    <div className="rounded-lg border border-border bg-white p-4 text-sm shadow-card">
      <div className="mb-1 font-semibold">{asset.asset_type}</div>
      <div className="text-slate-700">{asset.copy_text}</div>
    </div>
  )
}

