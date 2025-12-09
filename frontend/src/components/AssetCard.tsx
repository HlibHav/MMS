export default function AssetCard({ asset }: { asset: any }) {
  return (
    <div className="bg-white rounded-lg shadow p-4 border text-sm">
      <div className="font-semibold mb-1">{asset.asset_type}</div>
      <div className="text-gray-700">{asset.copy_text}</div>
    </div>
  )
}

