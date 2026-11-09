const integer = new Intl.NumberFormat('en-US')
const dollars = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 0,
})

export const EMPTY = '—'

export const formatInteger = (value) => (value == null ? EMPTY : integer.format(value))
export const formatCurrency = (value) => (value == null ? EMPTY : dollars.format(value))
export const formatPercent = (value, digits = 1) =>
  value == null ? EMPTY : `${(value * 100).toFixed(digits)}%`


export function formatValue(value, unit) {
  if (value == null) return EMPTY
  switch (unit) {
    case 'customers':
      return formatInteger(value)
    case 'share':
      return formatPercent(value, 1)
    case 'currency':
      return formatCurrency(value)
    case 'months':
      return `${value.toFixed(1)} months`
    default:
      return String(value)
  }
}