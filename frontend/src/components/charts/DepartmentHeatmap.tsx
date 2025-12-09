import { ResponsiveContainer, Treemap } from 'recharts'

interface DeptPoint {
  name: string
  gap_pct: number
  sales_value: number
}

export default function DepartmentHeatmap({ data }: { data: DeptPoint[] }) {
  const treeData = [
    {
      name: 'departments',
      children: data.map(d => ({
        name: d.name,
        size: Math.abs(d.gap_pct || 0),
        gap_pct: d.gap_pct ?? 0,
      })),
    },
  ]
  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <Treemap
          data={treeData}
          dataKey="size"
          stroke="#fff"
          content={(props) => {
            const { x, y, width, height, name, payload } = props as any
            if (!payload || width === undefined || height === undefined) return null

            const gap = payload?.gap_pct ?? 0
            const color = gap >= 0 ? '#10b981' : '#ef4444'
            return (
              <g>
                <rect x={x} y={y} width={width} height={height} style={{ fill: color, opacity: 0.8 }} />
                <text x={x + 4} y={y + 18} fill="#fff" fontSize={12}>
                  {name}
                </text>
              </g>
            )
          }}
        />
      </ResponsiveContainer>
    </div>
  )
}
