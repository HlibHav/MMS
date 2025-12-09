export default function CreativeBriefView({ brief }: { brief: any }) {
  return (
    <div className="space-y-2 text-sm">
      <div className="font-semibold">Objectives</div>
      <ul className="list-disc list-inside text-gray-700">
        {(brief.objectives || []).map((o: string, idx: number) => <li key={idx}>{o}</li>)}
      </ul>
      <div>
        <div className="font-semibold">Messaging</div>
        <div className="text-gray-700">{brief.messaging}</div>
      </div>
      <div className="text-gray-700">Tone: {brief.tone}</div>
      <div className="text-gray-700">Style: {brief.style}</div>
      <div className="font-semibold">Mandatory elements</div>
      <ul className="list-disc list-inside text-gray-700">
        {(brief.mandatory_elements || []).map((m: string, idx: number) => <li key={idx}>{m}</li>)}
      </ul>
    </div>
  )
}

