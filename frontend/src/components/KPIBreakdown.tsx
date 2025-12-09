export default function KPIBreakdown({ kpi }: { kpi: any }) {
  if (!kpi) return null
  return (
    <div className="space-y-2 text-sm">
      <div className="flex justify-between"><span>Sales</span><span className="font-semibold">{kpi.total_sales}</span></div>
      <div className="flex justify-between"><span>Margin</span><span className="font-semibold">{kpi.total_margin}</span></div>
      <div className="flex justify-between"><span>EBIT</span><span className="font-semibold">{kpi.total_ebit}</span></div>
      <div className="flex justify-between"><span>Units</span><span className="font-semibold">{kpi.total_units}</span></div>
    </div>
  )
}

