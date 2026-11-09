import { formatCurrency, formatInteger, formatPercent } from '../format'
import BreakdownChart from './BreakdownChart'

function BreakdownTable({ rows }) {
  return (
    <div className="mt-2 overflow-x-auto">
      <table className="w-full text-left tabular-nums">
        <thead className="text-xs text-muted">
          <tr>
            <th className="py-1.5 pr-3 font-medium">Group</th>
            <th className="px-3 py-1.5 text-right font-medium">Customers</th>
            <th className="px-3 py-1.5 text-right font-medium">Observed churn</th>
            <th className="px-3 py-1.5 text-right font-medium">Avg. predicted</th>
            <th className="py-1.5 pl-3 text-right font-medium">Revenue at risk (12 mo)</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.label} className="border-t border-line">
              <th scope="row" className="py-1.5 pr-3 font-normal">{row.label}</th>
              <td className="px-3 py-1.5 text-right">{formatInteger(row.customers)}</td>
              <td className="px-3 py-1.5 text-right">{formatPercent(row.observed_churn_rate)}</td>
              <td className="px-3 py-1.5 text-right">{formatPercent(row.avg_predicted_probability)}</td>
              <td className="py-1.5 pl-3 text-right">{formatCurrency(row.revenue_at_risk_12m)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function BreakdownPanel({ title, rows, layout }) {
  return (
    <section className="rounded-lg border border-line bg-panel p-4">
      <h3 className="font-medium">{title}</h3>
      <p className="mt-1 text-xs text-muted">
        Dark bars: churn counted from known outcomes. Light bars: the model's average predicted
        probability for the same customers.
      </p>
      <BreakdownChart rows={rows} layout={layout} />
      <details className="mt-3">
        <summary className="cursor-pointer text-muted">Show the numbers</summary>
        <BreakdownTable rows={rows} />
      </details>
    </section>
  )
}