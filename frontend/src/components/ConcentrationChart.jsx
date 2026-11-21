import {
  Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import { formatPercent } from '../format'
import { concentrationRows } from '../segments'

const CUSTOMERS = '#9db4ee'
const REVENUE = '#1d4ed8'
const tick = { fontSize: 12, fill: '#5b6575' }
const percent = (value) => formatPercent(value, 0)

export default function ConcentrationChart({ segments }) {
  const data = concentrationRows(segments)
  const height = Math.max(220, data.length * 56 + 70)

  return (
    <div style={{ height }} className="mt-3">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e3e6eb" horizontal={false} />
          <XAxis type="number" domain={[0, 1]} tickFormatter={percent} tick={tick} />
          <YAxis type="category" dataKey="label" width={200} tick={tick} />
          <Tooltip formatter={(value) => formatPercent(value, 1)} />
          <Legend />
          <Bar dataKey="customers" name="Share of customers" fill={CUSTOMERS} isAnimationActive={false} />
          <Bar dataKey="revenue" name="Share of revenue at risk" fill={REVENUE} isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}