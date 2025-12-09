import { PromoOpportunity } from '../types'

interface Props {
  opportunities?: PromoOpportunity[]
  onSelect?: (opp: PromoOpportunity) => void
}

export default function OpportunitiesList({ opportunities, onSelect }: Props) {
  if (!opportunities) return <div className="text-gray-500">No opportunities</div>
  return (
    <div className="space-y-2">
      {opportunities.map((opp) => (
        <div
          key={opp.id}
          className="border rounded p-3 hover:border-blue-500 cursor-pointer"
          onClick={() => onSelect?.(opp)}
        >
          <div className="font-semibold">{opp.department} - {opp.channel}</div>
          <div className="text-sm text-gray-600">Potential: {Math.round(opp.estimated_potential).toLocaleString()}</div>
          <div className="text-xs text-gray-500">Priority: {opp.priority}</div>
        </div>
      ))}
    </div>
  )
}

