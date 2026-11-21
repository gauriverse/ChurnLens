import { formatCurrency, formatInteger, formatMoney, formatPercent } from '../format'
import { historicalShare, segmentTotals } from '../segments'
import PriorityBadge from './PriorityBadge'

export default function SegmentTable({ segments }) {
  const totals = segmentTotals(segments)
  return (
    <div className="overflow-x-auto">
      <table className="w-full whitespace-nowrap text-left tabular-nums">
        <caption className="sr-only">Customer segments ordered by retention priority</caption>
        <thead className="text-xs text-muted">
          <tr>
            <th scope="col" className="py-2 pr-3 font-medium">Priority</th>
            <th scope="col" className="px-3 py-2 font-medium">Segment</th>
            <th scope="col" className="px-3 py-2 text-right font-medium">Customers</th>
            <th scope="col" className="px-3 py-2 text-right font-medium">Observed churn</th>
            <th scope="col" className="px-3 py-2 text-right font-medium">Avg. monthly charges</th>
            <th scope="col" className="px-3 py-2 text-right font-medium">Revenue at risk (12 mo)</th>
            <th
              scope="col"
              className="py-2 pl-3 text-right font-medium"
              title="Share of the monthly revenue lost to customers who actually churned. Counted from history, not estimated."
            >
              Share of churned revenue (historical)
            </th>
          </tr>
        </thead>
        <tbody>
          {segments.map((segment) => (
            <tr key={segment.cluster_id} className="border-t border-line align-top">
              <td className="py-2 pr-3">
                <span className="mr-2 font-medium">{`#${segment.retention_priority}`}</span>
                <PriorityBadge tier={segment.priority_tier} />
              </td>
              <th scope="row" className="px-3 py-2 text-left font-medium">{segment.persona_name}</th>
              <td className="px-3 py-2 text-right">
                {formatInteger(segment.size)}
                <span className="block text-xs text-muted">
                  {`${formatPercent(segment.share_of_customers)} of customers`}
                </span>
              </td>
              <td className="px-3 py-2 text-right">{formatPercent(segment.observed_churn_rate)}</td>
              <td className="px-3 py-2 text-right">{formatMoney(segment.avg_monthly_charges)}</td>
              <td className="px-3 py-2 text-right">
                {formatCurrency(segment.revenue_at_risk_12m)}
                <span className="block text-xs text-muted">
                  {`${formatPercent(segment.share_of_revenue_at_risk)} of total`}
                </span>
              </td>
              <td className="py-2 pl-3 text-right">{formatPercent(historicalShare(segment))}</td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr className="border-t border-line font-medium">
            <th scope="row" colSpan={2} className="py-2 pr-3 text-left">All segments</th>
            <td className="px-3 py-2 text-right">{formatInteger(totals.customers)}</td>
            <td className="px-3 py-2" />
            <td className="px-3 py-2" />
            <td className="px-3 py-2 text-right">{formatCurrency(totals.revenueAtRisk)}</td>
            <td className="py-2 pl-3" />
          </tr>
        </tfoot>
      </table>
    </div>
  )
}