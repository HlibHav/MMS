interface ScenarioRow {
  id: string
  name: string
  kpi: { total_sales: number; total_margin: number; total_ebit: number; total_units: number }
  status?: "PASS" | "WARN" | "BLOCK"
}

export default function ScenarioComparisonTable({
  scenarios,
  onSelect,
  onEdit,
  onDelete,
  onGenerateCreative,
}: {
  scenarios: ScenarioRow[]
  onSelect: (id: string) => void
  onEdit?: (id: string) => void
  onDelete?: (id: string) => void
  onGenerateCreative?: (id: string) => void
}) {
  return (
    <div className="overflow-x-auto text-sm">
      <table className="min-w-full divide-y divide-border">
        <thead>
          <tr>
            <th className="px-3 py-2 text-left">Scenario</th>
            <th className="px-3 py-2 text-left">Sales</th>
            <th className="px-3 py-2 text-left">Margin</th>
            <th className="px-3 py-2 text-left">EBIT</th>
            <th className="px-3 py-2 text-left">Units</th>
            <th className="px-3 py-2 text-left">Status</th>
            <th className="px-3 py-2 text-left">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border/60">
          {scenarios.map((s) => (
            <tr key={s.id} className="cursor-pointer transition hover:bg-surface-50" onClick={() => onSelect(s.id)}>
              <td className="px-3 py-2 font-medium text-slate-900">{s.name}</td>
              <td className="px-3 py-2">{s.kpi.total_sales}</td>
              <td className="px-3 py-2">{s.kpi.total_margin}</td>
              <td className="px-3 py-2">{s.kpi.total_ebit}</td>
              <td className="px-3 py-2">{s.kpi.total_units}</td>
              <td className="px-3 py-2">
                {s.status && (
                  <span
                    className={`rounded-full px-2 py-1 text-xs ${
                      s.status === "PASS" ? "bg-green-50 text-green-700" : s.status === "WARN" ? "bg-amber-50 text-amber-700" : "bg-red-50 text-red-700"
                    }`}
                  >
                    {s.status}
                  </span>
                )}
              </td>
              <td className="px-3 py-2 space-x-2">
                {onEdit && (
                  <button className="text-primary-700 underline" onClick={(e) => { e.stopPropagation(); onEdit(s.id); }}>
                    Edit
                  </button>
                )}
                {onGenerateCreative && (
                  <button className="text-primary-700 underline" onClick={(e) => { e.stopPropagation(); onGenerateCreative(s.id); }}>
                    Creative
                  </button>
                )}
                {onDelete && (
                  <button className="text-red-600 underline" onClick={(e) => { e.stopPropagation(); onDelete(s.id); }}>
                    Delete
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

