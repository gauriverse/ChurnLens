const STYLES = {
  High: 'bg-accent text-white',
  Medium: 'bg-accent-soft text-accent',
  Low: 'border border-line bg-canvas text-muted',
}

// Retention priority of a segment. Blue intensity, not the red/amber/green used for customer risk.
export default function PriorityBadge({ tier }) {
  return (
    <span className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${STYLES[tier] ?? STYLES.Low}`}>
      {tier} priority
    </span>
  )
}