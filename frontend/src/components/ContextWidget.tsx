import { PromoContext } from '../types'

export default function ContextWidget({ context }: { context?: PromoContext }) {
  if (!context) return <div className="text-muted">No context available</div>
  return (
    <div className="space-y-2 text-sm text-slate-700">
      <div className="font-semibold text-slate-900">Geo: {context.geo}</div>
      <div>
        <div className="font-semibold text-slate-900">Events</div>
        <ul className="list-disc list-inside">
          {(context.events || []).map((ev, idx) => (
            <li key={idx}>{ev.name} ({ev.date})</li>
          ))}
        </ul>
      </div>
      {context.weather && (
        <div>
          <div className="font-semibold text-slate-900">Weather</div>
          <pre className="rounded bg-surface-50 p-2 text-xs">{JSON.stringify(context.weather, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}

