export default function FactList({ items }) {
  return (
    <dl className="grid grid-cols-[auto_1fr] gap-x-6 gap-y-2">
      {items.map((item) => (
        <div key={item.label} className="contents">
          <dt className="text-muted">{item.label}</dt>
          <dd className="text-right font-medium tabular-nums">{item.value}</dd>
        </div>
      ))}
    </dl>
  )
}