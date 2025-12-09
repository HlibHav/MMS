import { PromoContext } from '../types'

export default function ContextWidget({ context }: { context?: PromoContext }) {
  if (!context) return <div className="text-gray-500">No context available</div>
  return (
    <div className="space-y-2 text-sm text-gray-700">
      <div className="font-semibold">Geo: {context.geo}</div>
      <div>
        <div className="font-semibold">Events</div>
        <ul className="list-disc list-inside">
          {(context.events || []).map((ev, idx) => (
            <li key={idx}>{ev.name} ({ev.date})</li>
          ))}
        </ul>
      </div>
      {context.weather && (
        <div>
          <div className="font-semibold">Weather</div>
          <pre className="text-xs bg-gray-50 p-2 rounded">{JSON.stringify(context.weather, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}

