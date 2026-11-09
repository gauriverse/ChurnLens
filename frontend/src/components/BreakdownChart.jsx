import {
  Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import { formatPercent } from '../format'

const OBSERVED = '#1d4ed8'
const PREDICTED = '#9db4ee'
const tick = { fontSize: 12, fill: '#5b6575' }
const percentTick = (value) => formatPercent(value, 0)
const tooltipValue = (value) => formatPercent(value, 1)

export default function BreakdownChart({ rows, layout = 'columns' }) {
  const data = rows.map((row) => ({
    label: row.label,
    observed: row.observed_churn_rate,
    predicted: row.avg_predicted_probability,
  }))
  const sideways = layout === 'rows'
  const height = sideways ? Math.max(200, rows.length * 56 + 70) : 260

  return (
    <div style={{ height }} className="mt-3">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          layout={sideways ? 'vertical' : 'horizontal'}
          margin={{ top: 8, right: 16, bottom: 0, left: 0 }}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="#e3e6eb"
            horizontal={!sideways}
            vertical={sideways}
          />
          <XAxis
            type={sideways ? 'number' : 'category'}
            dataKey={sideways ? undefined : 'label'}
            tickFormatter={sideways ? percentTick : undefined}
            tick={tick}
          />
          <YAxis
            type={sideways ? 'category' : 'number'}
            dataKey={sideways ? 'label' : undefined}
            width={sideways ? 190 : 56}
            tickFormatter={sideways ? undefined : percentTick}
            tick={tick}
          />
          <Tooltip formatter={tooltipValue} />
          <Legend />
          <Bar dataKey="observed" name="Observed churn" fill={OBSERVED} isAnimationActive={false} />
          <Bar
            dataKey="predicted"
            name="Model's average prediction"
            fill={PREDICTED}
            isAnimationActive={false}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}