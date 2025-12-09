interface ScenarioRow {
  id: string
  name: string
  kpi: { total_sales: number; total_margin: number; total_ebit: number; total_units: number }
}

export default function ScenarioComparisonTable({ scenarios, onSelect }: { scenarios: ScenarioRow[]; onSelect: (id: string) => void }) {
  return (
    <div className="overflow-x-auto text-sm">
      <table className="min-w-full divide-y divide-gray-200">
        <thead>
          <tr>
            <th className="px-3 py-2 text-left">Scenario</th>
            <th className="px-3 py-2 text-left">Sales</th>
            <th className="px-3 py-2 text-left">Margin</th>
            <th className="px-3 py-2 text-left">EBIT</th>
            <th className="px-3 py-2 text-left">Units</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {scenarios.map((s) => (
            <tr key={s.id} className="hover:bg-gray-50 cursor-pointer" onClick={() => onSelect(s.id)}>
              <td className="px-3 py-2 font-medium text-gray-900">{s.name}</td>
              <td className="px-3 py-2">{s.kpi.total_sales}</td>
              <td className="px-3 py-2">{s.kpi.total_margin}</td>
              <td className="px-3 py-2">{s.kpi.total_ebit}</td>
              <td className="px-3 py-2">{s.kpi.total_units}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

