import PriorityBadge from './PriorityBadge'

export default function SegmentCards({ segments }) {
  return (
    <ul className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      {segments.map((segment) => (
        <li key={segment.cluster_id} className="rounded-lg border border-line bg-panel p-4">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-medium">{segment.persona_name}</h3>
            <PriorityBadge tier={segment.priority_tier} />
          </div>
          <p className="mt-2 text-muted">
            {segment.description ?? 'No description is stored for this segment.'}
          </p>
        </li>
      ))}
    </ul>
  )
}