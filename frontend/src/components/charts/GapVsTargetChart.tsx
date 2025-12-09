import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Area, AreaChart } from 'recharts'

type Point = { date: string; actual: number; target: number }

export default function GapVsTargetChart({ data }: { data: Point[] }) {
  const gapData = data.map(d => ({ ...d, gap: d.actual - d.target }))
  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={gapData}>
          <defs>
            <linearGradient id="colorGap" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip />
          <Line type="monotone" dataKey="actual" stroke="#0ea5e9" dot={false} />
          <Line type="monotone" dataKey="target" stroke="#ef4444" dot={false} />
          <Area type="monotone" dataKey="gap" stroke="#0ea5e9" fillOpacity={1} fill="url(#colorGap)" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

