import { PromoOpportunity } from '../types'

interface Props {
  opportunities?: PromoOpportunity[]
  onSelect?: (opp: PromoOpportunity) => void
}

export default function OpportunitiesList({ opportunities, onSelect }: Props) {
  if (!opportunities) return <div className="text-muted">No opportunities</div>
  return (
    <div className="space-y-2">
      {opportunities.map((opp) => (
        <div
          key={opp.id}
          className="cursor-pointer rounded border border-border p-3 transition hover:border-primary-500 hover:bg-primary-50/60"
          onClick={() => onSelect?.(opp)}
        >
          <div className="font-semibold">{opp.department} - {opp.channel}</div>
          <div className="text-sm text-slate-600">Potential: {Math.round(opp.estimated_potential).toLocaleString()}</div>
          <div className="text-xs text-muted">Priority: {opp.priority}</div>
        </div>
      ))}
    </div>
  )
}

