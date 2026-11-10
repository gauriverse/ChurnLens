export const ALL_CUSTOMERS = 'All customers' 

export function mergeCurves(curves) {
  const months = [
    ...new Set(curves.flatMap((curve) => curve.points.map((point) => point.month))),
  ].sort((a, b) => a - b)
  const lookups = curves.map(
    (curve) => new Map(curve.points.map((point) => [point.month, point.survival])),
  )
  return months.map((month) => {
    const row = { month }
    curves.forEach((curve, index) => {
      row[curve.group] = lookups[index].get(month) ?? null 
    })
    return row
  })
}


export function monthTicks(maxMonth, step = 12) {
  const ticks = []
  for (let month = 0; month <= maxMonth; month += step) ticks.push(month)
  return ticks
}


export function visibleCurves(curves, contract) {
  if (!contract) return curves
  return curves.filter((curve) => curve.group === ALL_CUSTOMERS || curve.group === contract)
}

const GROUP_COLORS = {
  'All customers': '#111827',
  'Month-to-month': '#c2410c',
  'One year': '#1d4ed8',
  'Two year': '#0f766e',
}
const FALLBACK_COLORS = ['#7c3aed', '#be185d', '#4d7c0f']

export function groupColor(group, index) {
  return GROUP_COLORS[group] ?? FALLBACK_COLORS[index % FALLBACK_COLORS.length]
}