import { formatPercent } from './format'

// Totals across segments, from the API's own numbers
export function segmentTotals(segments) {
  return segments.reduce(
    (totals, segment) => ({
      customers: totals.customers + segment.size,
      revenueAtRisk: totals.revenueAtRisk + segment.revenue_at_risk_12m,
    }),
    { customers: 0, revenueAtRisk: 0 },
  )
}

// The historical share of churned revenue is stored with the segment's characteristics
export const historicalShare = (segment) =>
  segment.characteristics?.share_of_churned_revenue_historical ?? null

// One row per segment: share of customers next to share of revenue at risk
export function concentrationRows(segments) {
  return segments.map((segment) => ({
    label: segment.persona_name,
    customers: segment.share_of_customers,
    revenue: segment.share_of_revenue_at_risk,
  }))
}

// The headline of the concentration chart: the segment holding the most revenue at risk
export function topSegmentSummary(segments) {
  if (segments.length === 0) return null
  const top = [...segments].sort((a, b) => b.share_of_revenue_at_risk - a.share_of_revenue_at_risk)[0]
  return `${top.persona_name}: ${formatPercent(top.share_of_customers, 0)} of customers, ${formatPercent(top.share_of_revenue_at_risk, 0)} of the revenue at risk.`
}