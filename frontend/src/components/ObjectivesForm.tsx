interface Props {
  onSubmit: (values: any) => void
}

export default function ObjectivesForm({ onSubmit }: Props) {
  return (
    <form className="space-y-3 text-sm" onSubmit={(e) => { e.preventDefault(); onSubmit({}) }}>
      <div className="space-y-1">
        <label className="font-medium">Maximize</label>
        <select className="border rounded px-2 py-1 w-full">
          <option value="sales">Sales</option>
          <option value="margin">Margin</option>
          <option value="ebit">EBIT</option>
        </select>
      </div>
      <div className="space-y-1">
        <label className="font-medium">Min Margin %</label>
        <input className="border rounded px-2 py-1 w-full" defaultValue={20} type="number" />
      </div>
      <div className="space-y-1">
        <label className="font-medium">Max Discount %</label>
        <input className="border rounded px-2 py-1 w-full" defaultValue={25} type="number" />
      </div>
      <button className="bg-blue-600 text-white px-3 py-2 rounded" type="submit">Generate</button>
    </form>
  )
}

