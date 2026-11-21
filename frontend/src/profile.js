import { formatMoney, formatPercent } from './format'


export const REASON_CODE_LABELS = {
  NEW_CUSTOMER: 'Newer customer',
  MONTH_TO_MONTH: 'Month-to-month contract',
  HIGH_CHARGES: 'High monthly charges',
  ELECTRONIC_CHECK: 'Pays by electronic check',
  NO_SUPPORT_SERVICES: 'No tech support or online security',
  HIGH_VALUE_ACCOUNT: 'High-value account',
}


export const reasonCodeLabel = (code) =>
  Object.hasOwn(REASON_CODE_LABELS, code) ? REASON_CODE_LABELS[code] : code

export const sentenceCase = (text) => (text ? text.charAt(0).toUpperCase() + text.slice(1) : '')

export const outcomeLabel = (observedChurn) =>
  observedChurn === true ? 'Churned' : observedChurn === false ? 'Stayed' : 'Not known'


export function reasonBars(reasons) {
  const largest = Math.max(0, ...reasons.map((reason) => Math.abs(reason.contribution)))
  return reasons.map((reason) => ({
    rank: reason.rank,
    side: reason.direction === 'raises' ? 'right' : 'left',
    width: largest === 0 ? 0 : (Math.abs(reason.contribution) / largest) * 50,
  }))
}


export function describeAssumptions(assumptions) {
  if (!assumptions) return null
  const parts = []
  if (assumptions.offer_cost != null) parts.push(`offer cost ${formatMoney(assumptions.offer_cost)}`)
  if (assumptions.success_rate != null) parts.push(`${formatPercent(assumptions.success_rate, 0)} success rate`)
  if (assumptions.horizon_months != null) parts.push(`${assumptions.horizon_months} months of revenue kept`)
  if (assumptions.margin != null && assumptions.margin !== 1) {
    parts.push(`${formatPercent(assumptions.margin, 0)} margin`)
  }
  return parts.length ? parts.join(', ') : null
}


export function orderNotes(notes) {
  const rank = (note) => (note.level === 'warning' ? 0 : 1)
  return [...notes].sort((a, b) => rank(a) - rank(b))
}