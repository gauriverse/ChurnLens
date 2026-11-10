import {
  CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts'
import { formatPercent } from '../format'
import { ALL_CUSTOMERS, groupColor, mergeCurves, monthTicks } from '../survival'

const tick = { fontSize: 12, fill: '#5b6575' }

export default function SurvivalChart({ curves }) {
  const data = mergeCurves(curves)
  const lastMonth = data.at(-1)?.month ?? 0

  return (
    <div style={{ height: 320 }} className="mt-3">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 16, bottom: 16, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e3e6eb" vertical={false} />
          <XAxis
            dataKey="month"
            type="number"
            domain={[0, lastMonth]}
            ticks={monthTicks(lastMonth)}
            tick={tick}
            label={{ value: 'Tenure (months)', position: 'insideBottom', offset: -8, fill: '#5b6575', fontSize: 12 }}
          />
          <YAxis domain={[0, 1]} tickFormatter={(value) => formatPercent(value, 0)} width={56} tick={tick} />
          <Tooltip
            formatter={(value) => formatPercent(value, 1)}
            labelFormatter={(month) => `Month ${month}`}
          />
          <Legend verticalAlign="top" height={32} />
          {curves.map((curve, index) => {
            const overall = curve.group === ALL_CUSTOMERS
            return (
              <Line
                key={curve.group}
                type="stepAfter"
                dataKey={curve.group}
                stroke={groupColor(curve.group, index)}
                strokeWidth={overall ? 2 : 2.5}
                strokeDasharray={overall ? '6 4' : undefined}
                dot={false}
                isAnimationActive={false}
                connectNulls={false}
              />
            )
          })}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}