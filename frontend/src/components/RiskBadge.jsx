const STYLES = {
  Low: 'bg-risk-low-soft text-risk-low',
  Medium: 'bg-risk-medium-soft text-risk-medium',
  High: 'bg-risk-high-soft text-risk-high',
}

// The word carries the meaning; the colour only reinforces it.
export default function RiskBadge({ category }) {
  const style = STYLES[category] ?? 'bg-canvas text-muted'
  return (
    <span className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${style}`}>
      {category}
    </span>
  )
}